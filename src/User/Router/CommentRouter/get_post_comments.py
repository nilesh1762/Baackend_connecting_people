from fastapi import APIRouter, Depends, Query
from src.User.Controller.CommentController.get_paginated_post_comments_controller import get_paginated_post_comments_controller

from src.utils.db import init_db # Adjust this import to match your database session dependency
from sqlalchemy.orm import Session

user_router = APIRouter(prefix="/user", tags=["Comments"])

@user_router.get("/{post_id}/comments")
def get_post_comments(
    post_id: int,
    limit: int = Query(default=15, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(init_db)
):
    return get_paginated_post_comments_controller(
        post_id=post_id, 
        db=db, 
        limit=limit, 
        offset=offset
    )
