
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.User.model import PostModel, PostLikeModel

logger = logging.getLogger("telemetry")


def get_db_like_count(db: Session, post_id: int) -> int:
    """Helper function to fetch the aggregate like count directly from the database."""
    return db.query(func.count(PostLikeModel.id)).filter(
        PostLikeModel.post_id == post_id, 
        PostLikeModel.deleted_at.is_(None)
    ).scalar() or 0


def emit_ai_recommendation_event(user_id: int, post_id: int, action_type: str):
    """Handles telemetry formatting and non-blocking background stream logging."""
    ai_event_payload = {
        "user_id": user_id,
        "post_id": post_id,
        "interaction": action_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"AI_TELEMETRY_EVENT: {json.dumps(ai_event_payload)}")

def unlike_post_controller(db: Session, post_id: int, current_user_id: int, background_tasks) -> Dict[str, Any]:
    """Handles business logic for validating and executing a soft-delete on a post like."""
    like_record = db.query(PostLikeModel).filter(
        PostLikeModel.user_id == current_user_id,
        PostLikeModel.post_id == post_id,
        PostLikeModel.deleted_at.is_(None)
    ).first()

    if not like_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have not liked this post")

    # 🛠️ SOFT DELETE: Apply modern timestamp state preservation instead of erasing rows
    like_record.deleted_at = datetime.now(timezone.utc)
    db.commit()

    new_count = get_db_like_count(db, post_id)
    background_tasks.add_task(emit_ai_recommendation_event, current_user_id, post_id, "UNLIKE")

    return {"message": "Post unliked successfully", "like_count": new_count}