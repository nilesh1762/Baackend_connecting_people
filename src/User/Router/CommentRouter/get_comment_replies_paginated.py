from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from src.utils.db import init_db
from src.User.model import PostCommentModel

user_router = APIRouter(prefix="/user", tags=["Content Delivery"])

@user_router.get("/{comment_id}/replies", status_code=status.HTTP_200_OK)

def get_comment_replies_paginated(
    comment_id: int,
    limit: int = Query(default=5, ge=1, le=20), # Pull sub-threads in small 5-item chunks
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(init_db)
):
    """🌐 Fetches a paginated, reverse-chronological list of replies for a specific comment ID."""
    try:
        # 1. Calculate the total child count for UI tracking badges
        total_replies_count = db.query(PostCommentModel).filter(
            PostCommentModel.parent_comment_id == comment_id,
            PostCommentModel.is_deleted == False
        ).count()

        # 2. Extract paginated rows (Newest sub-replies first)
        db_replies = db.query(PostCommentModel).filter(
            PostCommentModel.parent_comment_id == comment_id,
            PostCommentModel.is_deleted == False
        ).order_by(PostCommentModel.created_at.asc()).offset(offset).limit(limit).all()

        # 3. Serialize output matching your React tree nodes
        serialized_replies = []
        for reply in db_replies:
            serialized_replies.append({
                "id": reply.id,
                "text": reply.text_content,
                "media_url": reply.media_url,
                "media_type": reply.media_type or ("image" if reply.media_url else None),
                "gif_url": reply.gif_url,
                "parent_comment_id": reply.parent_comment_id,
                "author_name": f"{reply.author.firstname} {reply.author.lastname}" if reply.author else "User",
                "author_avatar": reply.author.profile_image_url if reply.author else "",
                "created_at": reply.created_at.isoformat() if reply.created_at else None
            })

        return {
            "parent_id": comment_id,
            "total_count": total_replies_count,
            "replies": serialized_replies,
            "has_more": (offset + len(serialized_replies)) < total_replies_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load sub-replies graph thread: {str(e)}"
        )
