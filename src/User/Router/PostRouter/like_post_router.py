from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.PostController.like_post_controller import set_post_like_controller

user_router = APIRouter(prefix="/user", tags=["Post Metrics"])


@user_router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Like a post; repeating this request leaves it liked."""
    return set_post_like_controller(
        db=db,
        post_id=post_id,
        current_user_id=current_user_id,
        is_liked=True,
        background_tasks=background_tasks,
    )


@user_router.delete("/{post_id}/like", status_code=status.HTTP_200_OK)
def unlike_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Unlike a post through the same resource URL used to like it."""
    return set_post_like_controller(
        db=db,
        post_id=post_id,
        current_user_id=current_user_id,
        is_liked=False,
        background_tasks=background_tasks,
    )
