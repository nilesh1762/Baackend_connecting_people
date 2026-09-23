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


def like_post_controller(db: Session, post_id: int, current_user_id: int, background_tasks) -> Dict[str, Any]:
    """Handles business logic for validating, logging, or reactivating a post like."""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target post not found")

    existing_like = db.query(PostLikeModel).filter(
        PostLikeModel.user_id == current_user_id,
        PostLikeModel.post_id == post_id
    ).first()

    user_now_likes = False

    if existing_like:
        if existing_like.deleted_at is None:
            # 🚀 1. TOGGLE FIX (UNLIKE ACTION): If currently active, soft-delete it!
            # FIXED: Always use UTC timestamps for database logging consistency
            existing_like.deleted_at = datetime.now(timezone.utc)
            status_message = "Post unliked successfully"
            action_type = "UNLIKE"
        else:
            # 🚀 2. REACTIVATION: If it was previously soft-deleted, restore it
            existing_like.deleted_at = None
            user_now_likes = True
            status_message = "Post liked successfully"
            action_type = "LIKE"
    else:
        # 🚀 3. FRESH ROW REGISTRATION: Very first time like action
        new_like = PostLikeModel(user_id=current_user_id, post_id=post_id)
        db.add(new_like)
        user_now_likes = True
        status_message = "Post liked successfully"
        action_type = "LIKE"

    db.commit()

    # 🚀 4. PERFORMANCE CACHE BOUND: Sync the fresh count directly to POSTS_TABLE counter column
    # This prevents your global timeline feed queries from lagging under heavy calculation tasks
    fresh_db_count = db.query(func.count(PostLikeModel.id)).filter(
        PostLikeModel.post_id == post_id,
        PostLikeModel.deleted_at.is_(None)
    ).scalar() or 0
    post.likes_count = fresh_db_count
    db.commit()

    # Dispatch non-blocking telemetry event logs securely
    background_tasks.add_task(emit_ai_recommendation_event, current_user_id, post_id, action_type)

    return {
        "message": status_message,
        "is_liked": user_now_likes, # True if active like, False if unliked (Perfect for React UI icons toggling)
        "like_count": fresh_db_count
    }


