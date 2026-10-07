import os
import time
from typing import Dict, Any
import cloudinary.uploader
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import UserModel, MediaGalleryModel

def sync_banner_metadata_to_db(db: Session, current_user_id: int, secure_url: str, is_video: bool, upload_type: str) -> Dict[str, Any]:
    """
    Isolated database controller utility. Writes secure media URLs to user records,
    manages old column overrides, and commits the state cleanly.
    """
    user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile record not found.")

    # Apply database metadata modifications
    if is_video:
        user.cover_video_url = secure_url
        user.cover_image_url = None  # Clear image if video is active
    elif upload_type == "cover":
        user.cover_image_url = secure_url
        user.cover_video_url = None  # Clear video if image is active
    else:
        user.profile_image_url = secure_url
        
    db.commit()
    
    return {
        "status": "success",
        "message": f"Active {upload_type} synchronized successfully!",
        "cover_image_url": user.cover_image_url,
        "cover_video_url": user.cover_video_url,
        "profile_image_url": user.profile_image_url
    }
