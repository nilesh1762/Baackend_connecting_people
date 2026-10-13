from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from src.User.Controller.PostController.get_posts_feed_controller import (
    get_post_by_id_controller,
    get_posts_feed_controller,
)
from src.utils.db import init_db
from src.utils.security import get_current_user_id

from src.User.Schema.post_summary_Schema import PostDetailResponse, PostResponse

user_router = APIRouter(prefix="/user", tags=["User Relationships"])


@user_router.get(
    "/posts/{post_id}",
    response_model=PostDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_post_by_id(
    post_id: int,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Fetch one post for opening a shared post link."""
    return get_post_by_id_controller(
        db=db,
        post_id=post_id,
        current_user_id=current_user_id,
    )


@user_router.get("/feed", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
def get_posts_feed(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id) # Require auth to hide blocked content
):
     return get_posts_feed_controller(
        limit=limit,
        offset=offset,
        db=db,
        current_user_id=current_user_id
    )
