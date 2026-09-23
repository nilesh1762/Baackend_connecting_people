from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import func
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.model import PostModel, PostLikeModel
from src.User.Controller.un_like_post_controller import unlike_post_controller

user_router = APIRouter(prefix="/user", tags=["Engagement Engine"])

@user_router.delete("/{post_id}/unlike", status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """Soft-deletes an active engagement point by proxying parameters directly down to the controller layer."""
    return unlike_post_controller(
        db=db, 
        post_id=post_id, 
        current_user_id=current_user_id, 
        background_tasks=background_tasks
    )