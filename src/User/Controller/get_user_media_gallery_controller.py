from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.User.model import PostModel # Replace with your exact SQLAlchemy model path reference
from sqlalchemy import func, or_

def get_user_media_gallery_controller(db: Session, target_user_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
    """
    🔬 ULTIMATE COLUMN-TRACER MEDIA ENGINE
    Identifies hidden data layout configurations and extracts media records safely.
    """
    
    # ----------------------------------------------------
    # 🕵️‍♂️ THE LIVE COLUMN TRACER LOG: See the exact database values
    # ----------------------------------------------------
    raw_sample = db.query(PostModel).filter(
        or_(PostModel.author_id == target_user_id, PostModel.user_id == target_user_id)
    ).first()
    
    gallery_records = (
        db.query(PostModel)
        .filter(or_(PostModel.author_id == target_user_id, PostModel.user_id == target_user_id)) 
        .filter(or_(PostModel.is_deleted == False, PostModel.is_deleted.is_(None))) 
        
        # 🎯 THE FIX: Removed .media_url.isnot(None) and media_type filters entirely!
        # This allows standard text-only entries to pass through the database pipeline.
        
        .order_by(PostModel.created_at.desc()) 
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Package into a clean array structure for your React component
    serialized_gallery = []
    for post in gallery_records:
        # Determine fallback type layout string
        m_type = "text"
        if post.media_type:
            m_type = post.media_type.lower()

        serialized_gallery.append({
            "id": post.id,
            "type": m_type, # 🌟 Now safely defaults to "text" if no media exists
            "src": post.media_url, # Will be None for text-only posts
            "thumbnail_url": post.thumbnail_url or post.media_url, 
            "text_content": post.text_content, # 🌟 Your frontend reads this text caption row natively
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "views": "0" if not hasattr(post, 'views_count') else f"{post.views_count}",
            "likes": "0" if not hasattr(post, 'likes_count') else f"{post.likes_count}",
            "feeling": "0" if not hasattr(post, 'feeling') else f"{post.feeling}",
            "activity": "0" if not hasattr(post, 'activity') else f"{post.activity}",
            "checkin_place": "0" if not hasattr(post, 'checkin_place') else f"{post.checkin_place}",
            "checkin_metadata": "0" if not hasattr(post, 'checkin_metadata') else f"{post.checkin_metadata}",
            
            "author": {
                "id": post.author.id if post.author else target_user_id,
                "firstname": post.author.firstname if post.author else "Space",
                "lastname": (post.author.lastname or "") if post.author else "Explorer",
                "profile_image_url": (post.author.profile_image_url or "") if post.author else ""
            }
        })
        
    return serialized_gallery