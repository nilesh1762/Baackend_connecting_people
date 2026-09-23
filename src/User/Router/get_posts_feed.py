from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.User.Controller.get_posts_feed_controller import get_posts_feed_controller
from src.utils.db import init_db
from src.utils.security import get_current_user_id

from src.User.Schema.post_summary_Schema import PostResponse

user_router = APIRouter(prefix="/user", tags=["User Relationships"])

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
