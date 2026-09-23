from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case  
from src.User.model import BlockList, PostModel, PostLikeModel

def get_posts_feed_controller(
    limit: int,
    offset: int,
    db: Session,
    current_user_id: int
) -> list[dict]:
    """
    Retrieves the timeline feed while:
    1. Filtering out blocked/blocker content using high-performance anti-joins.
    2. Compiling real-time global like counts.
    3. Checking if the current user has personally liked each post via an Oracle-safe case expression.
    """
    
    # 1. Subquery to aggregate total likes across ALL posts
    total_likes_subq = (
        db.query(
            PostLikeModel.post_id,
            func.count(PostLikeModel.id).label("total_likes")
        )
        .filter(PostLikeModel.deleted_at.is_(None))  
        .group_by(PostLikeModel.post_id)
        .subquery()
    )

    # 2. Subquery to check if the CURRENT user liked each post
    user_liked_posts_subq = (
        db.query(PostLikeModel.post_id)
        .filter(
            PostLikeModel.user_id == current_user_id,
            PostLikeModel.deleted_at.is_(None)       
        )
        .subquery()
    )

    # 3. Main Query: Fetch posts, load authors, join metrics, and apply block filters
    query = (
        db.query(
            PostModel,
            func.coalesce(total_likes_subq.c.total_likes, 0).label("like_count"),
            case(
                (user_liked_posts_subq.c.post_id.is_not(None), 1),
                else_=0
            ).label("has_liked")
        )
        .options(joinedload(PostModel.author))  
        .outerjoin(total_likes_subq, PostModel.id == total_likes_subq.c.post_id)
        .outerjoin(user_liked_posts_subq, PostModel.id == user_liked_posts_subq.c.post_id)
        .filter(PostModel.author_id.is_not(None))
    )

    # 4. Performance Fix: Convert expensive '~in_' operators to correlated NOT EXISTS clauses
    query = query.filter(
        ~db.query(BlockList.id)
        .filter(BlockList.blocker_id == current_user_id, BlockList.blocked_id == PostModel.author_id)
        .exists()
    )

    query = query.filter(
        ~db.query(BlockList.id)
        .filter(BlockList.blocked_id == current_user_id, BlockList.blocker_id == PostModel.author_id)
        .exists()
    )

    # 5. Apply sorting, pagination, and execution
    results = (
        query.order_by(PostModel.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 6. Format into serializable dictionaries for your FastAPI endpoint
    feed = []
    for post, like_count, has_liked in results:
        if not post.author:
            continue
            
        feed.append({
            "id": post.id,
            "text_content": post.text_content,
            "media_url": post.media_url,
            "media_type": post.media_type,
            "created_at": post.created_at,
            "author": {
                "id": post.author.id,  
                "firstname": getattr(post.author, "firstname", "Unknown"),
                "lastname": getattr(post.author, "lastname", "User"),
                "username": getattr(post.author, "username", "Unknown"),
                "email": getattr(post.author, "email", ""),
                "profile_image_url": post.author.profile_image_url,
                "cover_image_url": post.author.cover_image_url,
                "cover_video_url,": post.author.cover_video_url,
                "created_at": post.author.created_at,
                
                # 🚀 FIX: Added these 4 required schema keys to satisfy Pydantic
                "dateofbirth": getattr(post.author, "dateofbirth", None),
                "gender": getattr(post.author, "gender", "Not Specified"),
                "mobilenumber": getattr(post.author, "mobilenumber", ""),
                "is_active": getattr(post.author, "is_active", True)
            },
            "like_count": like_count,
            "has_liked": bool(has_liked)
        })

    return feed
