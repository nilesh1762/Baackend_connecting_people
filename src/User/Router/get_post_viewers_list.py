from fastapi import APIRouter, Depends, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.get_post_viewers_list_controller import get_post_viewers_list_controller

user_router = APIRouter(prefix="/user", tags=["Post Metrics"])
@user_router.get("/{post_id}/viewers-list", status_code=status.HTTP_200_OK)
def get_post_viewers_list(
    post_id: int,
    limit: int = Query(default=10, ge=1, le=50), # Handles chunk size safely
    offset: int = Query(default=0, ge=0),       # Shifts index locations smoothly
    db: Session = Depends(init_db)
):
    return get_post_viewers_list_controller(db=db, post_id=post_id, limit=limit, offset=offset)
