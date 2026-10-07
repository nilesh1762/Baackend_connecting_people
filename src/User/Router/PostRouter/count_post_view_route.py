from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.PostController.increment_post_view_controller import increment_post_view_controller


user_router = APIRouter(prefix="/user", tags=["Post Metrics"])

@user_router.post("/{post_id}/view", status_code=status.HTTP_200_OK)
def log_post_view(
    post_id: int,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id) # Secured with login token
):
    """Record a unique view for the authenticated user and post."""
    return increment_post_view_controller(db=db, post_id=post_id, current_user_id=current_user_id)
