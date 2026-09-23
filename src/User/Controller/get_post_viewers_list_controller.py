from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any
from src.User.model import PostModel, PostViewModel, UserModel


def get_post_viewers_list_controller(db: Session, post_id: int, limit: int, offset: int):
    """
    Queries profile cards of users who viewed a post using strict database pagination boundaries.
    Safe for millions of rows.
    """
    # Query user rows using strict offset boundaries
    viewers_query = (
        db.query(UserModel)
        .join(PostViewModel, PostViewModel.user_id == UserModel.id)
        .filter(PostViewModel.post_id == post_id)
        .order_by(PostViewModel.created_at.desc()) # Newest viewers first
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Serialize only this small batch page array (e.g., 10 entries)
    serialized_viewers = []
    for viewer in viewers_query:
        serialized_viewers.append({
            "id": viewer.id,
            "firstname": viewer.firstname,
            "lastname": viewer.lastname or "",
            "profile_image_url": viewer.profile_image_url or ""
        })

    return {
        "post_id": post_id,
        "limit": limit,
        "offset": offset,
        "viewed_by_users": serialized_viewers # Returns ONLY 10 profiles at a time!
    }
