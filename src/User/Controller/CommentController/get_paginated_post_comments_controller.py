from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import Dict, Any
from src.User.model import PostCommentModel

def get_paginated_post_comments_controller(
    post_id: int, 
    db: Session, 
    limit: int = 15, 
    offset: int = 0
) -> Dict[str, Any]:
    
    # 1. Fetch only top-level (parent) comments
    # 🎯 FIXES BUG 1: Includes comments where is_deleted is NULL
    parent_comments = (
        db.query(PostCommentModel)
        .options(joinedload(PostCommentModel.author))
        .filter(
            and_(
                PostCommentModel.post_id == post_id,
                PostCommentModel.parent_comment_id == None,
                or_(PostCommentModel.is_deleted == False, PostCommentModel.is_deleted == None)
            )
        )
        .order_by(PostCommentModel.created_at.desc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    has_more = len(parent_comments) > limit
    parents_to_process = parent_comments[:limit] if has_more else parent_comments

    if not parents_to_process:
        return {"comments": [], "has_more": False, "next_offset": offset}

    parent_ids = [c.id for c in parents_to_process]

    # 2. Fetch all replies tied to this post safely
    all_replies = (
        db.query(PostCommentModel)
        .options(joinedload(PostCommentModel.author))
        .filter(
            and_(
                PostCommentModel.post_id == post_id,
                PostCommentModel.parent_comment_id.isnot(None),
                or_(PostCommentModel.is_deleted == False, PostCommentModel.is_deleted == None)
            )
        )
        .order_by(PostCommentModel.created_at.asc())
        .all()
    )

    # 🎯 FIXES BUG 2: Build a dynamic dictionary to prevent KeyError crashes
    replies_by_parent: Dict[int, list] = {}
    
    for reply in all_replies:
        pid = reply.parent_comment_id
        if pid not in replies_by_parent:
            replies_by_parent[pid] = []
            
        replies_by_parent[pid].append({
            "id": reply.id,
            "text": reply.text_content,
            "media_url": reply.media_url,
            "media_type": reply.media_type or ("image" if reply.media_url else None),
            "gif_url": reply.gif_url,
            "parent_comment_id": reply.parent_comment_id,
            "author": {
                "id": reply.author.id if reply.author else None,
                "name": f"{reply.author.firstname} {reply.author.lastname}" if reply.author else "Anonymous User",
                "avatar": reply.author.profile_image_url if reply.author else ""
            },
            "created_at": reply.created_at.isoformat() if reply.created_at else None
        })

    # 3. Build UI Payloads securely
    formatted_comments = []
    for parent in parents_to_process:
        formatted_comments.append({
            "id": parent.id,
            "text": parent.text_content,
            "media_url": parent.media_url,
            "media_type": parent.media_type or ("image" if parent.media_url else None),
            "gif_url": parent.gif_url,
            "parent_comment_id": None,
            "author": {
                "id": parent.author.id if parent.author else None,
                "name": f"{parent.author.firstname} {parent.author.lastname}" if parent.author else "Anonymous User",
                "avatar": parent.author.profile_image_url if parent.author else ""
            },
            "created_at": parent.created_at.isoformat() if parent.created_at else None,
            # Gracefully drops empty array instead of failing if parent has no replies
            "replies": replies_by_parent.get(parent.id, []) 
        })

    return {
        "comments": formatted_comments,
        "has_more": has_more,
        "next_offset": offset + len(formatted_comments)
    }
