from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.User.model import PostModel # Replace with your exact SQLAlchemy model path reference

def get_user_media_gallery_controller(db: Session, target_user_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
    """
    Queries only post records that contain valid video loops, images, or GIFs 
    uploaded strictly by the specific targeted user profile.
    """
    # 1. Execute targeted query filtering out text-only posts
    gallery_records = (
        db.query(PostModel)
        .filter(PostModel.author_id == target_user_id) # 🚀 FILTER 1: Only this user's posts
        # 🚀 FILTER 2: Exclude text-only posts by ensuring media columns are populated
        .filter(PostModel.is_deleted == False) 
        .filter(PostModel.media_url.isnot(None)) 
        .filter(PostModel.media_type.in_(["IMAGE", "GIF", "VIDEO"])) # Only target media formats
        .order_by(PostModel.created_at.desc()) # Newest items first
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # 2. Package into a clean dictionary list array matching your React MediaStreamsTab layout
    serialized_gallery = []
    for post in gallery_records:
        serialized_gallery.append({
            "id": post.id,
            "type": post.media_type.lower(), 
            "src": post.media_url,
            "thumbnail_url": post.thumbnail_url or post.media_url, 
            "text_content": post.text_content,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "views": "0" if not hasattr(post, 'views_count') else f"{post.views_count}",
            "likes": "0" if not hasattr(post, 'likes_count') else f"{post.likes_count}",
            "feeling": "0" if not hasattr(post, 'feeling') else f"{post.feeling}",
            "activity": "0" if not hasattr(post, 'activity') else f"{post.activity}",
            "checkin_place": "0" if not hasattr(post, 'checkin_place') else f"{post.checkin_place}",
            "checkin_metadata": "0" if not hasattr(post, 'checkin_metadata') else f"{post.checkin_metadata}",
            
 
            # 🚀 NEW: NESTED AUTHOR INFO FOR YOUR FRONTEND UI CHIPS
            "author": {
                "id": post.author.id if post.author else target_user_id,
                "firstname": post.author.firstname if post.author else "Space",
                "lastname": (post.author.lastname or "") if post.author else "Explorer",
                "profile_image_url": (post.author.profile_image_url or "") if post.author else ""
            }
        })
        
    return serialized_gallery
