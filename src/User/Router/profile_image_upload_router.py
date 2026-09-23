from fastapi import APIRouter, Depends, status, UploadFile, File,Form
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.utils.security import get_current_user_id
# 🚀 Explicitly import the isolated controller actions
from src.User.Controller.upload_profile_image_controller import upload_profile_image_controller, delete_profile_image_controller

user_router = APIRouter(prefix="/user", tags=["User Relationships"])


@user_router.post("/upload_image", status_code=status.HTTP_200_OK)
async def upload_profile_image(
    imageFile: UploadFile = File(...),              #  FIXED: Matches 'imageFile' key from React
    upload_type: str = Form(...),                   #  NEW: Matches 'uploadType' ('avatar' or 'cover')
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Accepts a raw profile form payload to create or overwrite assets."""
    # Pass both parameters cleanly to your controller handler
    return upload_profile_image_controller(
        db=db, 
        current_user_id=current_user_id, 
        file=imageFile, 
        upload_type=upload_type
    )


@user_router.delete("/delete_image", status_code=status.HTTP_200_OK)
async def delete_profile_image(
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Deletes the active avatar image from the cloud storage bucket and clears the database reference field."""
    return delete_profile_image_controller(db=db, current_user_id=current_user_id)
