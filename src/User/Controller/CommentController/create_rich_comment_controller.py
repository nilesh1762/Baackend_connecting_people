import os

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from src.User.model import PostCommentModel
from src.User.model import PostModel
from src.utils.setting import get_settings

settings = get_settings()
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 100 * 1024 * 1024

def create_rich_comment_controller(
    post_id: int,
    current_user_id: int,
    text_content: str = None,
    file: UploadFile = None,
    attached_gif_url: str = None,
    parent_comment_id: int = None,
    db: Session = None
) -> PostCommentModel:
    """🎬 Process multi-channel input parameters and write clean comment records safely."""
    
    # Guardrail Check: Disallow blank inputs
    if not text_content and not file and not attached_gif_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Comment content cannot be entirely empty."
        )

    saved_media_url = None
    media_type = None

    # A. Handle Binary Device File Uploads to Cloudinary
    if file and file.filename:
        content_type = (file.content_type or "").lower()
        if content_type.startswith("image/"):
            media_type = "gif" if content_type == "image/gif" else "image"
            resource_type = "image"
            max_size = MAX_IMAGE_SIZE
        elif content_type.startswith("video/"):
            media_type = "video"
            resource_type = "video"
            max_size = MAX_VIDEO_SIZE
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment attachments must be an image or video.",
            )

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > max_size:
            max_size_mb = max_size // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Comment {media_type} files must be under {max_size_mb}MB.",
            )

        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"user_comments/user_{current_user_id}/post_{post_id}",
                resource_type=resource_type,
            )
            saved_media_url = upload_result.get("secure_url")
            if not saved_media_url:
                raise RuntimeError("Cloudinary did not return a secure media URL.")
        except Exception as upload_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cloud comment media storage process failed: {str(upload_error)}"
            )

    # B. Execute Isolated Atomic State Database Commit
    try:
        with db.begin_nested(): # Safe transactional savepoint guard
            new_comment = PostCommentModel(
                post_id=post_id,
                author_id=current_user_id,
                text_content=text_content if text_content else None,
                media_url=saved_media_url,
                media_type=media_type,
                gif_url=attached_gif_url,
                parent_comment_id=parent_comment_id
            )
            db.add(new_comment)
            
            # C. Automatically increment the interaction counter cache on the parent post
            parent_post = db.query(PostModel).filter(PostModel.id == post_id).first()
            if parent_post:
                parent_post.comments_count = (getattr(parent_post, "comments_count", 0) or 0) + 1

        db.commit() # Flush transaction modifications together cleanly
        db.refresh(new_comment)
        return new_comment

    except Exception as db_fault:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database state engine failed to save comment transaction: {str(db_fault)}"
        )
