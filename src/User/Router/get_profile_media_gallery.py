from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.User.Controller.get_user_media_gallery_controller import get_user_media_gallery_controller

router = APIRouter(prefix="/user", tags=["User Media Gallery"])

@router.get("/profile/{user_id}/media", status_code=status.HTTP_200_OK)
async def get_profile_media_gallery(
    user_id: int,
    limit: int = Query(default=12, ge=1, le=50), # 12 items matches a standard 3-column desktop grid perfectly!
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(init_db)
):
    """
    Fetches a sanitized, media-only asset feed grid matching a specific user ID registry entry.
    """
    return get_user_media_gallery_controller(db=db, target_user_id=user_id, limit=limit, offset=offset)
