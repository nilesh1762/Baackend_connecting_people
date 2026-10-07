from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.utils.db import init_db
from src.utils.security import get_current_user_id
# Import your new controller function
from src.User.Controller.CommentController.remove_comment_controller import remove_comment_controller

# Initialize your router here (or import it if defined elsewhere)
user_router = APIRouter(prefix="/user", tags=["Content Delivery"])

@user_router.delete("/delete-comments/{comment_id}", status_code=status.HTTP_200_OK)
def soft_delete_social_comment(
    comment_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(init_db)
):
    """🗑️ Route mapping for comment soft-deletion."""
    return remove_comment_controller(comment_id=comment_id, current_user_id=current_user_id, db=db)
