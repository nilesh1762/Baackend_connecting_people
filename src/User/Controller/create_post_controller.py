import json
import os
import ffmpeg
import shutil # This ensures the binary file streams transfer into the temporary processing directory perfectly without dropping data packets.
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import PostModel, PostTagModel 
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
    """Processes images, GIFs, and videos via Cloudinary, managing normalized states and auto-thumbnails."""
    
    # 1. Base Gatekeeper Guardrail Validation (Updated to check for new interactive layers too)
    if not text_content and not file and not feeling and not activity and not checkin_json:
        raise HTTPException(status_code=400, detail="Post content cannot be entirely empty.")

    saved_media_url = None
    detected_media_type = None
    saved_thumbnail_url = None

    # 2. Process File Ingestion if provided (Your working pure-python hachoir parser block)
    if file and file.filename:
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        content_type = (file.content_type or "").lower()
        
        if content_type in ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]:
            if file_size > MAX_IMAGE_SIZE:
                raise HTTPException(status_code=400, detail="Image files must be under 10MB.")
        
            detected_media_type = "GIF" if "gif" in content_type else "IMAGE"
            resource_kind = "image"

        elif content_type.startswith("video/"):
            if file_size > MAX_VIDEO_SIZE:
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
                        raise HTTPException(status_code=400, detail="The file does not contain readable video duration tracking parameters.")

                    duration = metadata.get("duration").total_seconds()

                os.remove(temp_path)
                temp_path = None 
                file.file.seek(0)

                LIMIT_SECONDS = 140.0
                if duration > LIMIT_SECONDS:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Video duration limits exceeded. Max allowed length is {int(LIMIT_SECONDS)} seconds."
                    )
                    
            except HTTPException as http_error:
                raise http_error
            except Exception as metadata_fault:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)  
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid or corrupted video payload structural format provided."
                )

            detected_media_type = "VIDEO"
            resource_kind = "video"  
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported media format '{content_type}'. Use images, GIFs, or videos."
            )

        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"user_posts/user_{current_user_id}/{resource_kind}s", 
                resource_type=resource_kind
            )
            saved_media_url = upload_result.get("secure_url")

            if detected_media_type == "VIDEO" and saved_media_url:
                base_url, _ = os.path.splitext(saved_media_url)
                saved_thumbnail_url = f"{base_url}.jpg"

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cloud media upload pipeline step failed: {str(e)}"
            )

    # 🚀 3. Parse incoming checkin payload text string safely
    parsed_place_name = None
    if checkin_json:
        try:
            parsed_checkin = json.loads(checkin_json)
            parsed_place_name = (
            parsed_checkin.get('name', {}).get('display_name') or
            parsed_checkin.get('city', {}).get('display_name') or
            parsed_checkin.get('rawDetails', {}).get('display_name')
        )
            # print("placename==", parsed_checkin)
            # print("checkin_json==", checkin_json)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid layout formatting for checkin parameters.")

    # 4. Commit Structured Metadata Record to Oracle Database
    new_post = PostModel(
        user_id=current_user_id,
        author_id=current_user_id,
        text_content=text_content,
        media_url=saved_media_url,
        media_type=detected_media_type,
        thumbnail_url=saved_thumbnail_url,
        
        #  Added  new database column map assignments here
        feeling=feeling,
        activity=activity,
        checkin_place=parsed_place_name,
        checkin_metadata=checkin_json  # Stored directly as a raw stringified JSON object
    )
    
    db.add(new_post)
    db.commit()      # 👈 Triggers structural save row transaction block
    db.refresh(new_post)

    # 👥 5. Process Friend Tagging Junction Row Insertions
    if tagged_friends_json:
        try:
            friend_ids = json.loads(tagged_friends_json)
            if isinstance(friend_ids, list):
                for friend_id in friend_ids:
                    # Map the generated new_post.id with target user link keys
                    tagged_entry = PostTagModel(post_id=new_post.id, user_id=friend_id)
                    db.add(tagged_entry)
                db.commit()  # Flush tag rows safely
        except ValueError:
            pass # Fail gracefully if incoming string format is corrupted

    return new_post

