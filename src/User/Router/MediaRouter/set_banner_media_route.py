from fastapi import APIRouter, Depends, Body, status, HTTPException
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.media_controller import sync_banner_metadata_to_db


banner_router = APIRouter(prefix="/user", tags=["User Relationships"])

@banner_router.put("/media/set-banner", status_code=status.HTTP_200_OK)
def set_active_banner_from_gallery(
  
    payload: dict = Body(...), 
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db)
):
    """
    Allows a user to choose a past file from their Cloud Gallery Hub 
    and instantly apply it as their active dashboard backdrop.
    """
    secure_url = payload.get("secure_url")
    media_type = payload.get("media_type") # "image" or "video"

    print("media==", secure_url, media_type)
    if not secure_url:
        raise HTTPException(status_code=400, detail="Missing secure_url path parameter.")

    # 🟢 EXECUTE THE REUSED CODE PIPELINE INSTANTLY!
    return sync_banner_metadata_to_db(
        db=db,
        current_user_id=current_user_id,
        secure_url=secure_url,
        is_video=(media_type == "video"),
        upload_type="cover" # Instructs the model matrix to apply fields to background covers
    )
