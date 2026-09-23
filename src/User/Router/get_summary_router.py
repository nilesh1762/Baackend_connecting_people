from typing import List
from fastapi import Query, APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload 
from src.utils.db import init_db
from src.User.model import PostModel
from src.User.Schema.post_summary_Schema import PostResponse
 # 1. Import joinedload
# Make sure your other local imports (router, PostResponse, init_db, PostModel) are present

user_router = APIRouter(prefix="/user", tags=["Content Delivery"])

@user_router.get("/get_summary", response_model=List[PostResponse], status_code=status.HTTP_200_OK)
def get_posts_feed(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(init_db)
):
    """Retrieves standard timelines sorted by newest creation records with authors."""
    posts = (
        db.query(PostModel)
        .options(joinedload(PostModel.author))  # Force-loads the author object row metrics immediately
        .order_by(PostModel.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # 🚀 FastAPI intercepts this return array, validates it via PostResponse, 
    # and appends your like, dislike, and share counts into the JSON automatically!
    return posts

