from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any
from src.User.model import PostModel, PostViewModel, UserModel
import logging
from src.utils.db import init_db

logger = logging.getLogger(__name__)

def increment_post_view_controller(db: Session, post_id: int, current_user_id: int) -> Dict[str, Any]:
    """
    Validates post existence, filters out repeat view logs from the same user identity, 
    and locks down unique analytical metrics tracking counters.
    """
    # 1. Locate the target profile post row
    db: Session = next(init_db()) 
    
    try:
      post = db.query(PostModel).filter(PostModel.id == post_id).first()
      if not post:
        return {"views_count": 0, "status": "not_found"}

     # Unique Check Filter
      already_viewed = db.query(PostViewModel).filter(
        PostViewModel.user_id == current_user_id,
        PostViewModel.post_id == post_id
       ).first()

      if already_viewed:
        return {"views_count": post.views_count, "status": "already_viewed"}

     # Register brand new unique view row
      new_view_log = PostViewModel(user_id=current_user_id, post_id=post_id)
      db.add(new_view_log)
      post.views_count += 1
      db.commit()
      db.refresh(post)

      return {"views_count": post.views_count, "status": "success"}
        
    except Exception as db_error:
        db.rollback()
        logger.error(f"BACKGROUND_VIEW_TRANSACTION_FAILED: {str(db_error)}")
    finally:
        # 🚀 CRUCIAL: Always close the session to return the connection to the pool
        db.close() 
