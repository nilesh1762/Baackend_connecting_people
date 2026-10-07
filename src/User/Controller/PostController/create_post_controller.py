import json
import os
import ffmpeg
import shutil # This ensures the binary file streams transfer into the temporary processing directory perfectly without dropping data packets.
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import PostModel, PostTagModel ,UserModel
import cloudinary
import cloudinary.uploader
from src.utils.setting import get_settings
from tempfile import NamedTemporaryFile
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

settings = get_settings()

# Initialize Cloudinary Configuration
cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True
)

# Constrain boundaries (e.g., 10MB image limit, 100MB video maximum limit over buffers)
MAX_IMAGE_SIZE = 1024 * 1024 * 10   # Strict 10MB Image Cap
MAX_VIDEO_SIZE = 1024 * 1024 * 100  # Strict 100MB Video Cap

def create_post_controller(
    text_content: Optional[str],
    file: Optional[UploadFile],
    feeling: Optional[str] = None,
    activity: Optional[str] = None,
    checkin_json: Optional[str] = None,
    tagged_friends_json: Optional[str] = None,
    db: Session = None,
    current_user_id: int = None
) -> Any:
    """Processes text, quotes, images, and videos via Cloudinary, managing system announcements and tags."""
    
    # ----------------------------------------------------
    # 1. Base Gatekeeper Guardrail Validation
    # ----------------------------------------------------
    if not text_content and not file and not feeling and not activity and not checkin_json:
        raise HTTPException(status_code=400, detail="Post content cannot be entirely empty.")

    saved_media_url = None
    detected_media_type = None
    saved_thumbnail_url = None

    # ----------------------------------------------------
    # 2. Process File Ingestion if provided (Images / Videos)
    # ----------------------------------------------------
    if file and file.filename:
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        content_type = (file.content_type or "").lower()
        
        # A. Process Image Uploads
        if content_type in ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]:
            if file_size > 10 * 1024 * 1024: # 10MB Limit
                raise HTTPException(status_code=400, detail="Image files must be under 10MB.")
        
            detected_media_type = "gif" if "gif" in content_type else "image"
            resource_kind = "image"

        # B. Process Video Uploads
        elif content_type.startswith("video/"):
            if file_size > 100 * 1024 * 1024: # 100MB Limit
                raise HTTPException(status_code=400, detail="Video files must be under 100MB.")
            
            file.file.seek(0)
            temp_path = None
            try:
                with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                    shutil.copyfileobj(file.file, temp_file)
                    temp_path = temp_file.name

                with createParser(temp_path) as parser:
                    if not parser:
                        raise Exception("Unable to parse file stream headers.")    
                    metadata = extractMetadata(parser)
                    if not metadata or not metadata.has("duration"):
                        raise HTTPException(status_code=400, detail="The file does not contain readable duration parameters.")

                    duration = metadata.get("duration").total_seconds()

                os.remove(temp_path)
                temp_path = None 
                file.file.seek(0)

                if duration > 140.0:
                    raise HTTPException(status_code=400, detail="Video duration limits exceeded. Max allowed length is 140 seconds.")
                    
            except HTTPException as http_error:
                raise http_error
            except Exception:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)  
                raise HTTPException(status_code=400, detail="Invalid or corrupted video payload structural format.")

            detected_media_type = "video"
            resource_kind = "video"  
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported media format '{content_type}'. Use images, GIFs, or videos.")

        # C. Cloudinary Transfer Execution
        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"user_posts/user_{current_user_id}/{resource_kind}s", 
                resource_type=resource_kind
            )
            saved_media_url = upload_result.get("secure_url")

            if detected_media_type == "video" and saved_media_url:
                base_url, _ = os.path.splitext(saved_media_url)
                saved_thumbnail_url = f"{base_url}.jpg"

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cloud media upload pipeline step failed: {str(e)}"
            )

    # ----------------------------------------------------
    # 3. 🎯 THE TEXT FILTER MECHANISM (If no file is attached)
    # ----------------------------------------------------
    else:
        # Check if the author is an official app account profile to automatically flag announcements
        current_user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
        
        if current_user and current_user.profile_category == "System":
            detected_media_type = "system_announcement"
        
        # If the status starts with quotes and is reasonably short, label it as a quote component
        elif text_content and text_content.strip().startswith(('"', "'", "“", "‘")) and len(text_content) < 280:
            detected_media_type = "quote"
        
        else:
            detected_media_type = "text"

    # ----------------------------------------------------
    # 4. Parse Incoming Checkin JSON Payload String
    # ----------------------------------------------------
    parsed_place_name = None
    if checkin_json:
        try:
            parsed_checkin = json.loads(checkin_json)
            parsed_place_name = (
                parsed_checkin.get('name', {}).get('display_name') or
                parsed_checkin.get('city', {}).get('display_name') or
                parsed_checkin.get('rawDetails', {}).get('display_name')
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid layout formatting for checkin parameters.")

    # ----------------------------------------------------
    # 5. Commit Structured Metadata Record to Database
    # ----------------------------------------------------
    new_post = PostModel(
        user_id=current_user_id,
        author_id=current_user_id,
        text_content=text_content,
        media_url=saved_media_url,
        media_type=detected_media_type, # 🌟 Saves as: video, image, system_announcement, quote, or text
        thumbnail_url=saved_thumbnail_url,
        feeling=feeling,
        activity=activity,
        checkin_place=parsed_place_name,
        checkin_metadata=checkin_json  
    )
    
    db.add(new_post)
    db.commit()      
    db.refresh(new_post)

    # ----------------------------------------------------
    # 6. Process Friend Tagging Junction Row Insertions
    # ----------------------------------------------------
    if tagged_friends_json:
        try:
            friend_ids = json.loads(tagged_friends_json)
            if isinstance(friend_ids, list):
                for friend_id in friend_ids:
                    tagged_entry = PostTagModel(post_id=new_post.id, user_id=friend_id)
                    db.add(tagged_entry)
                db.commit()  
        except ValueError:
            pass # Fail silently if string layout is unparseable

    return new_post