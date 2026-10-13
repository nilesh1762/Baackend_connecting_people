from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.PostController.like_post_controller import set_post_like_controller

user_router = APIRouter(prefix="/user", tags=["Engagement Engine"])


@user_router.delete("/{post_id}/unlike", status_code=status.HTTP_200_OK)
def unlike_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Unlike a post; repeating this request leaves it unliked."""
    return set_post_like_controller(
        db=db,
        post_id=post_id,
        current_user_id=current_user_id,
        is_liked=False,
        background_tasks=background_tasks,
    )