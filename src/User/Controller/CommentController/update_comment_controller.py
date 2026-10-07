import logging
import os
from urllib.parse import unquote, urlsplit

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.User.model import PostCommentModel
from src.utils.setting import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 100 * 1024 * 1024


def _cloudinary_public_id(media_url: str) -> str | None:
    if not media_url or "cloudinary.com" not in media_url:
        return None

    path = urlsplit(media_url).path
    if "/upload/" not in path:
        return None

    uploaded_path = path.split("/upload/", 1)[1]
    segments = uploaded_path.split("/")
    version_index = next(
        (index for index, segment in enumerate(segments) if segment.startswith("v") and segment[1:].isdigit()),
        None,
    )
    if version_index is not None:
        segments = segments[version_index + 1 :]
    if not segments:
        return None

    public_id = "/".join(segments)
    filename, extension_separator, _ = public_id.rpartition(".")
    if extension_separator:
        public_id = filename
    return unquote(public_id) or None


def _destroy_cloudinary_asset(media_url: str, media_type: str | None) -> bool:
    public_id = _cloudinary_public_id(media_url)
    if not public_id:
        return True

    resource_type = "video" if media_type == "video" else "image"
    result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
    return result.get("result") == "ok"


def update_comment_controller(
    comment_id: int,
    current_user_id: int,
    db: Session,
    text_content: str | None = None,
    attached_gif_url: str | None = None,
    file: UploadFile | None = None,
    clear_media: bool = False,
    clear_gif: bool = False,
) -> dict:
    comment = (
        db.query(PostCommentModel)
        .filter(PostCommentModel.id == comment_id)
        .first()
    )

    if not comment or comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    if comment.author_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments.",
        )

    if clear_media and file and file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a replacement media file or clear_media, not both.",
        )

    has_file = bool(file and file.filename)
    if clear_gif and attached_gif_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide an updated GIF URL or clear_gif, not both.",
        )

    if text_content is None and attached_gif_url is None and not has_file and not clear_media and not clear_gif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one comment field to update.",
        )

    replacement_media_url = None
    replacement_media_type = None
    replacement_public_id = None
    if file and file.filename:
        content_type = (file.content_type or "").lower()
        if content_type.startswith("image/"):
            replacement_media_type = "gif" if content_type == "image/gif" else "image"
            resource_type = "image"
            max_size = MAX_IMAGE_SIZE
        elif content_type.startswith("video/"):
            replacement_media_type = "video"
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
                detail=f"Comment {replacement_media_type} files must be under {max_size_mb}MB.",
            )

        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"user_comments/user_{current_user_id}/post_{comment.post_id}",
                resource_type=resource_type,
            )
            replacement_media_url = upload_result.get("secure_url")
            replacement_public_id = upload_result.get("public_id")
            if not replacement_media_url:
                raise RuntimeError("Cloudinary did not return a secure media URL.")
        except Exception as upload_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Comment media upload failed: {upload_error}",
            ) from upload_error

    previous_media_url = comment.media_url
    previous_media_type = comment.media_type or ("image" if previous_media_url else None)

    try:
        if text_content is not None:
            comment.text_content = text_content.strip() or None
        if attached_gif_url is not None:
            comment.gif_url = attached_gif_url.strip() or None
        if clear_gif:
            comment.gif_url = None
        if clear_media:
            comment.media_url = None
            comment.media_type = None
        elif replacement_media_url:
            comment.media_url = replacement_media_url
            comment.media_type = replacement_media_type

        if not comment.text_content and not comment.media_url and not comment.gif_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A comment must contain text, an uploaded image/video, or a GIF URL.",
            )

        db.commit()
        db.refresh(comment)
    except HTTPException:
        db.rollback()
        if replacement_public_id:
            try:
                cloudinary.uploader.destroy(
                    replacement_public_id,
                    resource_type=resource_type,
                )
            except Exception:
                logger.exception("Failed to clean up an unused replacement comment asset.")
        raise
    except SQLAlchemyError as error:
        db.rollback()
        if replacement_public_id:
            try:
                cloudinary.uploader.destroy(
                    replacement_public_id,
                    resource_type=resource_type,
                )
            except Exception:
                logger.exception("Failed to clean up an unused replacement comment asset.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment.",
        ) from error

    cleanup_warning = None
    if (clear_media or replacement_media_url) and previous_media_url:
        try:
            if not _destroy_cloudinary_asset(previous_media_url, previous_media_type):
                cleanup_warning = "The old uploaded media could not be removed from storage."
        except Exception:
            logger.exception("Failed to delete replaced comment media from Cloudinary.")
            cleanup_warning = "The old uploaded media could not be removed from storage."

    response = {
        "success": True,
        "comment_id": comment.id,
        "text_content": comment.text_content,
        "media_url": comment.media_url,
        "media_type": comment.media_type,
        "gif_url": comment.gif_url,
        "parent_comment_id": comment.parent_comment_id,
        "post_id": comment.post_id,
    }
    if cleanup_warning:
        response["media_cleanup_warning"] = cleanup_warning
    return response
