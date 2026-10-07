import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.User.model import PostModel, PostViewModel

logger = logging.getLogger(__name__)


def increment_post_view_controller(
    db: Session, post_id: int, current_user_id: int
) -> Dict[str, Any]:
    """Record one view per authenticated user and post."""
    try:
        post = (
            db.query(PostModel)
            .filter(PostModel.id == post_id)
            .with_for_update()
            .first()
        )
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        already_viewed = (
            db.query(PostViewModel)
            .filter(
                PostViewModel.user_id == current_user_id,
                PostViewModel.post_id == post_id,
            )
            .first()
        )
        if already_viewed:
            return {"views_count": post.views_count, "status": "already_viewed"}

        db.add(PostViewModel(user_id=current_user_id, post_id=post_id))
        post.views_count += 1
        db.commit()
        return {"views_count": post.views_count, "status": "success"}

    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to record view for post_id=%s and user_id=%s",
            post_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to record post view",
        ) from None
