import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.User.model import PostModel, PostLikeModel

logger = logging.getLogger("telemetry")


def emit_ai_recommendation_event(user_id: int, post_id: int, action_type: str):
    ai_event_payload = {
        "user_id": user_id,
        "post_id": post_id,
        "interaction": action_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"AI_TELEMETRY_EVENT: {json.dumps(ai_event_payload)}")


def set_post_like_controller(
    db: Session,
    post_id: int,
    current_user_id: int,
    is_liked: bool,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Set a user's like state for a post and synchronize its cached count."""
    try:
        post = (
            db.query(PostModel)
            .filter(
                PostModel.id == post_id,
                PostModel.moderation_status == "approved",
            )
            .with_for_update()
            .first()
        )
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target post not found",
            )

        like = (
            db.query(PostLikeModel)
            .filter(
                PostLikeModel.user_id == current_user_id,
                PostLikeModel.post_id == post_id,
            )
            .first()
        )
        was_liked = like is not None and like.deleted_at is None

        if is_liked and not was_liked:
            if like is None:
                db.add(PostLikeModel(user_id=current_user_id, post_id=post_id))
            else:
                like.deleted_at = None
        elif not is_liked and like is not None and like.deleted_at is None:
            like.deleted_at = datetime.now(timezone.utc)

        db.flush()
        like_count = (
            db.query(func.count(PostLikeModel.id))
            .filter(
                PostLikeModel.post_id == post_id,
                PostLikeModel.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )
        post.likes_count = like_count
        db.commit()

        changed = was_liked != is_liked
        if changed:
            action_type = "LIKE" if is_liked else "UNLIKE"
            background_tasks.add_task(
                emit_ai_recommendation_event,
                current_user_id,
                post_id,
                action_type,
            )

        return {
            "message": "Post liked successfully" if is_liked else "Post unliked successfully",
            "is_liked": is_liked,
            "like_count": like_count,
        }
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to update like for post_id=%s and user_id=%s",
            post_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update post like",
        ) from None
