from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.User.model import PostModel, PostShareModel, UserModel

def log_post_share_controller(db: Session, current_user_id: int, post_id: int, platform: str = "internal") -> Dict[str, Any]:
    """
    Validates post existence, handles Twitter-style single-share toggling,
    increments high-speed counters, and returns the details of the sharing user.
    """
    # 1. Locate the target post item row record
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Target post record not found."
        )

    # 2. Isolate the current user row to package their profile details for the response
    current_user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User identity profile data row not found."
        )

    # 3. Check if this post was shared by this specific user previously
    existing_share = db.query(PostShareModel).filter(
        PostShareModel.user_id == current_user_id,
        PostShareModel.post_id == post_id
    ).first()

    user_now_shares = False

    # 4. 🚀 THE SAFETY WORKFLOW: Wrap transactions inside a try-except block
    try:
        if existing_share:
            # 🔄 TWITTER-STYLE "UNDO SHARE" PATH: Remove share row record from table
            db.delete(existing_share)
            status_message = "Share undone successfully"
        else:
            # 🔄 FIRST-TIME SHARE PATH: Create a transactional record tracking share data
            new_share = PostShareModel(
                user_id=current_user_id, 
                post_id=post_id, 
                platform_target=platform 
            )
            db.add(new_share)
            user_now_shares = True
            status_message = f"Post shared externally to {platform} successfully! 🚀"

        # Commit structural row additions or deletions first
        db.commit()
        
        # 5. 🚀 COUNTER CALCULATIONS SYNC: Recalculate live total rows from logs table
        fresh_share_count = db.query(PostShareModel).filter(PostShareModel.post_id == post_id).count()
        
        # Explicitly overwrite the integer column inside the POSTS_TABLE row directly!
        post.shares_count = fresh_share_count
        db.commit()
        db.refresh(post) # Refreshes model data to capture live row calculations
        
    except Exception as database_transaction_error:
        db.rollback() # Rolls back changes if transaction layers snap or fail
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database sharing transaction failed: {str(database_transaction_error)}"
        )

    # 6. 🚀 RETURN VALUES WITH SHARING USER DETAILS INCLUDED
    return {
        "message": status_message,
        "post_id": post_id, 
        "shares_count": post.shares_count,
        "is_shared": user_now_shares, # True if active share, False if undone (Perfect for React UI)
        "user_details": {
            "id": current_user.id,
            "firstname": current_user.firstname,
            "lastname": current_user.lastname,
            "profile_image_url": current_user.profile_image_url or ""
        }
    }
