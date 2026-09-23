from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import func
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.model import PostModel, PostLikeModel
from src.User.Controller.like_post_controller import like_post_controller
user_router = APIRouter(prefix="/user", tags=["Post Metrics"])

@user_router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
async def like_post(
    post_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """Registers an engagement point by proxying input properties straight down to the controller layer."""
    return like_post_controller(
        db=db, 
        post_id=post_id, 
        current_user_id=current_user_id, 
        background_tasks=background_tasks
    )

@user_router.delete("/{post_id}/unlike", status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """Applies a soft-delete timestamp marker to an active user engagement row."""
    like_record = db.query(PostLikeModel).filter(
        PostLikeModel.user_id == current_user_id,
        PostLikeModel.post_id == post_id,
        PostLikeModel.deleted_at.is_(None)  # 🔍 Only select currently active likes
    ).first()

    if not like_record:
        raise HTTPException(status_code=400, detail="You have not liked this post")

    # 🛠️ SOFT DELETE: Update with current system timestamp instead of hard deleting
    like_record.deleted_at = datetime.now(timezone.utc)
    db.commit()

    new_count = get_db_like_count(db, post_id)
    background_tasks.add_task(emit_ai_recommendation_event, current_user_id, post_id, "UNLIKE")

    return {"message": "Post unliked successfully", "like_count": new_count}
