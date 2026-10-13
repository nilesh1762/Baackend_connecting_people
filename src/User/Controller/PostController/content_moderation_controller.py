import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from src.User.model import PostModel

logger = logging.getLogger(__name__)


def get_pending_post_media_controller(
    db: Session,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    try:
        posts = (
            db.query(PostModel)
            .options(joinedload(PostModel.author))
            .filter(
                PostModel.moderation_status == "pending",
                PostModel.media_url.is_not(None),
                PostModel.is_deleted == False,
            )
            .order_by(PostModel.created_at.asc(), PostModel.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to retrieve pending post media")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve pending media.",
        ) from None

    return [
        {
            "id": post.id,
            "text_content": post.text_content,
            "media_url": post.media_url,
            "media_type": post.media_type,
            "thumbnail_url": post.thumbnail_url,
            "created_at": post.created_at,
            "author": {
                "id": post.author.id,
                "firstname": post.author.firstname,
                "lastname": post.author.lastname,
            } if post.author else None,
        }
        for post in posts
    ]


def moderate_post_media_controller(
    db: Session,
    post_id: int,
    decision: str,
) -> dict[str, Any]:
    if decision not in {"approved", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approved' or 'rejected'.",
        )

    try:
        post = (
            db.query(PostModel)
            .filter(
                PostModel.id == post_id,
                PostModel.moderation_status == "pending",
                PostModel.media_url.is_not(None),
                PostModel.is_deleted == False,
            )
            .with_for_update()
            .first()
        )
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending media post not found.",
            )

        post.moderation_status = decision
        db.commit()
        return {"post_id": post.id, "moderation_status": decision}
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to moderate post_id=%s", post_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update post moderation status.",
        ) from None
