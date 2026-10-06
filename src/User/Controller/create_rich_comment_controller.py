from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
import cloudinary.uploader
from src.User.model import PostCommentModel
from src.User.model import PostModel

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

    # A. Handle Binary Device File Uploads to Cloudinary
    if file and file.filename:
        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"user_comments/user_{current_user_id}/post_{post_id}",
                resource_type="image"
            )
            saved_media_url = upload_result.get("secure_url")
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
