from datetime import datetime, timezone # Added for timestamp tracking
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.User.model import PostCommentModel
from datetime import datetime, timezone

def remove_comment_controller(comment_id: int, current_user_id: int, db: Session):
    """🗑️ Enterprise Soft-Delete Business Logic Layer."""
    comment = db.query(PostCommentModel).filter(PostCommentModel.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")

    # Security Rule Check
    if comment.author_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized action footprint.")

    try:
        # Flag true instead of purging the database row
        comment.is_deleted = True

        # Decrement counter metrics cache on the parent post dynamically
        if comment.post:
            comment.post.comments_count = max(0, (comment.post.comments_count or 1) - 1)
        
        db.commit()
        return {"success": True, "comment_id": comment_id, "post_id": comment.post_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database state mutation fault: {str(e)}"
        )