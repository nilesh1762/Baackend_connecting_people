import os
from typing import Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import UserModel, MediaGalleryModel
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader  # 🚀 IMPORT CLOUDINARY UPLOADER
from src.utils.setting import get_settings
import time
import uuid

settings = get_settings()
# Load .env variables
load_dotenv()

# Initialize Cloudinary Configuration
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,  # Uses lowercase from Option B
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True                                 # Forces secure HTTPS URLs
)

# 5MB File Size Boundary Constraint
MAX_FILE_SIZE = 5242880 
# Configuration size matrices for large scale deployments
MAX_IMAGE_SIZE = 1024 * 1024 * 5   # 5MB Image limit
MAX_VIDEO_SIZE = 1024 * 1024 * 50  # 20MB Video limit for short looped b-rolls

def upload_profile_image_controller(db: Session, current_user_id: int, file: UploadFile, upload_type: str) -> Dict[str, Any]:
    # 1. Detect Media Archetype Format 
    is_video = file.content_type.startswith("video/")
    is_image = file.content_type.startswith("image/")

    if not is_image and not is_video:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unsupported format. File must be an image (PNG, JPG) or video (MP4, WEBM)."
        )

    # 2. Dynamic Size Verification Constraints
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0) # Reset file buffer stream reader pointer index

    allowed_max_size = MAX_VIDEO_SIZE if is_video else MAX_IMAGE_SIZE
    if file_size > allowed_max_size:
        size_label = "20MB" if is_video else "5MB"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File exceeds maximum allowed limit of {size_label}."
        )

    user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile record not found.")

    # 3. Dynamic Path & Bucket Resolution Setup
    timestamp_key = int(time.time())
    
    # Organize asset destinations cleanly based on file types
    if is_video:
        target_folder = "cover_videos"
        old_url = user.cover_video_url # Maps your Oracle DB video column row
        resource_kind = "video"        # 🚀 CRUCIAL: Cloudinary media bucket switch key [5, 6]
    else:
        target_folder = "covers" if upload_type == "cover" else "avatars"
        old_url = user.cover_image_url if upload_type == "cover" else user.profile_image_url
        resource_kind = "image"

    # 4. Clear Out Old Assets from Cloudinary Cloud Buckets
    if old_url:
        try:
            url_parts = old_url.split("/")
            folder_index = url_parts.index(target_folder)
            public_id_with_ext = "/".join(url_parts[folder_index:])
            public_id = os.path.splitext(public_id_with_ext)[0]
            
            # Passes explicit dynamic resource_type indicators to clear legacy file paths completely [5, 6]
            cloudinary.uploader.destroy(public_id, resource_type=resource_kind)
        except Exception as e:
            print(f"Failed to clear old asset for user_{current_user_id}: {str(e)}")

    # 5. Stream Binary Payload Stream Directly onto Cloudinary
    try:
        unique_suffix = uuid.uuid4().hex[:6]

        upload_result = cloudinary.uploader.upload(
            file.file,
            folder=target_folder,
            public_id=f"user_{current_user_id}_{upload_type}_{timestamp_key}_{unique_suffix}",
            overwrite=True,
            resource_type=resource_kind # 🚀 FIXED: Tells Cloudinary whether to treat this file as a video or image [5, 6]
        )
        uploaded_url = upload_result.get("secure_url")

        cloudinary_public_id = upload_result.get("public_id")
         
        gallery_record = MediaGalleryModel(
            user_id=current_user_id,
            media_type="video" if is_video else "image",
            secure_url=uploaded_url,
            public_id=cloudinary_public_id
        )
        db.add(gallery_record)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Cloudinary pipeline upload crash event: {str(e)}"
        )

    # 6. Synchronize Metadata Directly to Database Columns Mapping
    if is_video:
        user.cover_video_url = uploaded_url
    elif upload_type == "cover":
        user.cover_image_url = uploaded_url
        user.cover_video_url = None # Clear out any existing video if user explicitly changes back to an image static asset
    else:
        user.profile_image_url = uploaded_url
        
    db.commit()
    try:
        db.refresh(gallery_record)
    except Exception as e:
        print(f"Session sync notice (non-blocking): {str(e)}")
    
    return {
        "message": f"{upload_type.capitalize()} uploaded successfully", 
        "profile_image_url": uploaded_url 
    }
def delete_profile_image_controller(db: Session, current_user_id: int) -> Dict[str, Any]:
    """Wipes the avatar file from Cloudinary and reverts the database pointer to NULL."""
    user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile record not found.")

    if not user.profile_image_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No profile image exists to delete.")

    # 1. Erase file from Cloudinary
    try:
        url_parts = user.profile_image_url.split("/")
        public_id_with_ext = "/".join(url_parts[-2:])
        public_id = os.path.splitext(public_id_with_ext)[0]
        
        cloudinary.uploader.destroy(public_id) [7]
    except Exception as e:
        print(f"Cloudinary deletion failed: {str(e)}")

    # 2. Remove the database reference
    user.profile_image_url = None
    db.commit()

    return {"message": "Profile image deleted successfully"}
