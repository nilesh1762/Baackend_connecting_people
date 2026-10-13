from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy import func, desc, case, exists, and_, literal, or_, union_all
from typing import Dict, Any

from src.User.model import (
    UserModel,
    PostModel,
    PostRepostModel,
    Friendship,
    PostCommentModel,
)

def get_first_time_dashboard_feed_controller(current_user_id: int, db: Session, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    # ----------------------------------------------------
    # STEP 1: Fetch Current Logged-In User Details
    # ----------------------------------------------------
    current_user = db.query(UserModel).filter(UserModel.id == current_user_id).first()
    if not current_user:
        return {"user_segment": "Personalized", "feed": [], "has_more": False, "next_offset": 0}

    # ----------------------------------------------------
    # STEP 2: Define Author Alias for Clear Table Isolations
    # ----------------------------------------------------
    AuthorModel = aliased(UserModel, name="post_author")

    # ----------------------------------------------------
    # STEP 3: Dynamic Social Graph Personalization
    # ----------------------------------------------------
    is_friend_condition = exists().where(
        and_(
            Friendship.user_id == current_user_id,
            Friendship.friend_id == PostModel.author_id, 
            Friendship.is_deleted == False
        )
    )

    base_weight = case(
        (func.lower(func.trim(PostModel.media_type)) == "system_announcement", 200),
        (is_friend_condition, 100),
        (func.lower(func.trim(AuthorModel.city)) == func.lower(func.trim(current_user.city)), 50),
        else_=1
    )

    feed_score = (
        base_weight + 
        (PostModel.likes_count * 3) + 
        (PostModel.shares_count * 5) + 
        (PostModel.views_count * 1)
    ).label("feed_score")

    # ----------------------------------------------------
    # STEP 4: Query the Personalized Target Feed
    # ----------------------------------------------------
    original_entries = db.query(
        PostModel.id.label("post_id"),
        PostModel.created_at.label("feed_created_at"),
        literal(0).label("is_repost"),
        literal(None, type_=PostRepostModel.id.type).label("repost_id"),
        literal(None, type_=UserModel.id.type).label("reposter_id"),
        literal("anyone").label("visibility"),
    ).filter(
        PostModel.is_deleted == False,
        PostModel.author_id.is_not(None),
        PostModel.author_id != current_user_id,
        PostModel.moderation_status == "approved",
    )
    repost_entries = db.query(
        PostRepostModel.post_id.label("post_id"),
        PostRepostModel.created_at.label("feed_created_at"),
        literal(1).label("is_repost"),
        PostRepostModel.id.label("repost_id"),
        PostRepostModel.user_id.label("reposter_id"),
        PostRepostModel.visibility.label("visibility"),
    ).join(
        PostModel, PostModel.id == PostRepostModel.post_id
    ).filter(
        PostModel.is_deleted == False,
        PostModel.author_id.is_not(None),
        PostModel.moderation_status == "approved",
        or_(
            PostRepostModel.visibility == "anyone",
            PostRepostModel.user_id == current_user_id,
            exists().where(
                and_(
                    Friendship.user_id == PostRepostModel.user_id,
                    Friendship.friend_id == current_user_id,
                    Friendship.is_deleted == False,
                )
            ),
        ),
    )
    all_feed_entries = union_all(
        original_entries,
        repost_entries,
    ).subquery("all_feed_entries")
    ranked_feed_entries = db.query(
        all_feed_entries.c.post_id,
        all_feed_entries.c.feed_created_at,
        all_feed_entries.c.is_repost,
        all_feed_entries.c.repost_id,
        all_feed_entries.c.reposter_id,
        all_feed_entries.c.visibility,
        func.row_number().over(
            partition_by=all_feed_entries.c.post_id,
            order_by=(
                case(
                    (all_feed_entries.c.reposter_id == current_user_id, 1),
                    else_=0,
                ).desc(),
                all_feed_entries.c.is_repost.desc(),
                all_feed_entries.c.feed_created_at.desc(),
                all_feed_entries.c.repost_id.desc(),
            ),
        ).label("entry_rank"),
    ).subquery("ranked_feed_entries")
    feed_entries = db.query(
        ranked_feed_entries.c.post_id,
        ranked_feed_entries.c.feed_created_at,
        ranked_feed_entries.c.is_repost,
        ranked_feed_entries.c.repost_id,
        ranked_feed_entries.c.reposter_id,
        ranked_feed_entries.c.visibility,
    ).filter(
        ranked_feed_entries.c.entry_rank == 1,
    ).subquery("feed_entries")
    ReposterModel = aliased(UserModel, name="post_reposter")

    raw_posts = db.query(
        PostModel,
        feed_score,
        feed_entries.c.feed_created_at,
        feed_entries.c.is_repost,
        feed_entries.c.repost_id,
        feed_entries.c.visibility,
        ReposterModel,
    ).join(
        feed_entries, PostModel.id == feed_entries.c.post_id
    ).join(
        AuthorModel, PostModel.author_id == AuthorModel.id
    ).outerjoin(
        ReposterModel, ReposterModel.id == feed_entries.c.reposter_id
    ).options(
        selectinload(PostModel.comments_log).selectinload(PostCommentModel.author)
    ).order_by(
        feed_score.desc(),  
        feed_entries.c.feed_created_at.desc(),
        PostModel.id.desc(),
    ).offset(offset).limit(limit + 1).all()

    has_more = len(raw_posts) > limit
    posts_to_process = raw_posts[:limit] if has_more else raw_posts

    # ----------------------------------------------------
    # STEP 5: Transform Database Tuples into UI Component Data
    # ----------------------------------------------------
    formatted_feed = []
    for (
        post,
        score,
        feed_created_at,
        is_repost,
        repost_id,
        feed_visibility,
        reposter,
    ) in posts_to_process:
        layout_type = "STANDARD_TEXT"
        post_comments_array = []

        # Sort with newest comments first
        sorted_db_comments = sorted(post.comments_log, key=lambda c: c.created_at, reverse=True)
       
        
        # We only take the top 3 parent comments initially. 
        # This keeps the initial timeline feed fast and responsive.
        parent_comment_counter = 0
        for comment in sorted_db_comments:
            if not comment.is_deleted:
                # If it's a top-level comment, increment our display limit tracking
                if not comment.parent_comment_id:
                    parent_comment_counter += 1
                
                # Stop appending once we have reached our limit of 3 parent comment threads
                if parent_comment_counter > 3:
                    continue

                post_comments_array.append({
                    "id": comment.id,
                    "text": comment.text_content,
                    "media_url": comment.media_url,
                    "media_type": comment.media_type or ("image" if comment.media_url else None),
                    "gif_url": comment.gif_url,
                    "parent_comment_id": comment.parent_comment_id, 
                    "author_id": comment.author_id,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "author_name": f"{comment.author.firstname} {comment.author.lastname}" if comment.author else "Anonymous User",
                    "author_avatar": comment.author.profile_image_url if comment.author else ""
                })

        m_type = (post.media_type or "").lower().strip()
        if "video" in m_type:
            layout_type = "VIDEO_PLAYER"
        elif "image" in m_type or "photo" in m_type:
            layout_type = "IMAGE_GALLERY"
        elif "quote" in m_type:
            layout_type = "QUOTE_CARD"

        post_data = {
            "post_id": post.id,
            "feed_item_id": f"repost:{repost_id}" if is_repost else f"post:{post.id}",
            "is_repost": bool(is_repost),
            "visibility": feed_visibility,
            "feed_created_at": feed_created_at.isoformat() if feed_created_at else None,
            "reposted_at": feed_created_at.isoformat() if is_repost and feed_created_at else None,
            "reposted_by": {
                "id": reposter.id,
                "name": f"{reposter.firstname} {reposter.lastname}",
                "avatar": reposter.profile_image_url or "",
            } if is_repost and reposter else None,
            "layout_type": layout_type,
            "score_weight": int(score),
            # 🎯 FIXED: Convert datetime objects to string format to prevent JSON crash loops
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "author": {
                "id": post.author.id,
                "name": f"{post.author.firstname} {post.author.lastname}",
                "avatar": post.author.profile_image_url or ""
            },
            "engagement": {
                "likes_count": post.likes_count or 0,
                "has_liked": False,
                "comments_count": post.comments_count or 0,
                "views_count": post.views_count or 0,
            },
            "comments": post_comments_array, 
            "components": {
                "text_layer": { "body": post.text_content },
                "media_layer": {
                    "url": post.media_url,
                    "thumbnail": post.thumbnail_url,
                    "aspect_ratio": "16:9" if layout_type == "VIDEO_PLAYER" else "1:1"
                } if layout_type in ["VIDEO_PLAYER", "IMAGE_GALLERY"] else None,
                "quote_layer": {
                    "text": post.text_content,
                    "author": post.author.firstname
                } if layout_type == "QUOTE_CARD" else None
            }
        }
        formatted_feed.append(post_data)

    return {
        "user_segment": "Personalized",
        "feed": formatted_feed,
        "has_more": has_more,
        "next_offset": offset + len(formatted_feed)
    }
