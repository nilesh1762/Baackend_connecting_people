from fastapi import APIRouter, Depends, status,Query
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.User.model import MediaGalleryModel # Ensure your MediaGalleryModel is imported
from src.utils.security import get_current_user_id

gallery_router = APIRouter(prefix="/user", tags=["User Relationships"])

@gallery_router.get("/media/gallery")

def get_user_media_gallery(
    # 💡 Optional filtering: React can pass "?media_filter=image" or "?media_filter=video"
    media_filter: str | None = Query(default=None), 
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db)
):
    """
    Fetches the media history collection belonging explicitly to the logged-in user.
    Guarantees user isolation so users can never see each other's uploaded content.
    """
    # 1. 🛡️ STRICT SECURITY FILTER: Query records matching ONLY the active token user ID
    query = db.query(MediaGalleryModel).filter(MediaGalleryModel.user_id == current_user_id)
  
    # 2. Apply media category type filters if requested by the frontend tabs
    if media_filter in ["image", "video"]:
        query = query.filter(MediaGalleryModel.media_type == media_filter)
        
    # 3. Sort by latest upload timestamp first and execute
    gallery_items = query.order_by(MediaGalleryModel.created_at.desc()).all()
   
    # 4. Map records cleanly into a structured network response array
    return [
        {
            "id": row.id,
            "media_type": row.media_type,
            "secure_url": row.secure_url,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in gallery_items
    ]
