import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, aliased, joinedload, selectinload
from sqlalchemy import and_, case, exists, func, literal, or_, union_all
from sqlalchemy.exc import SQLAlchemyError
from src.User.model import (
    BlockList,
    Friendship,
    PostLikeModel,
    PostModel,
    PostRepostModel,
    UserModel,
)

logger = logging.getLogger(__name__)


def get_post_by_id_controller(db: Session, post_id: int, current_user_id: int) -> dict:
    """Fetch one visible post for an authenticated user."""
    try:
        post = (
            db.query(PostModel)
            .options(
                joinedload(PostModel.author),
                selectinload(PostModel.tagged_friends),
            )
            .filter(
                PostModel.id == post_id,
                PostModel.is_deleted == False,
                PostModel.author_id.is_not(None),
                PostModel.moderation_status == "approved",
                ~db.query(BlockList.id)
                .filter(
                    BlockList.blocker_id == current_user_id,
                    BlockList.blocked_id == PostModel.author_id,
                )
                .exists(),
                ~db.query(BlockList.id)
                .filter(
                    BlockList.blocked_id == current_user_id,
                    BlockList.blocker_id == PostModel.author_id,
                )
                .exists(),
            )
            .first()
        )
        if post is None or post.author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found.",
            )

        has_liked = (
            db.query(PostLikeModel.id)
            .filter(
                PostLikeModel.post_id == post_id,
                PostLikeModel.user_id == current_user_id,
                PostLikeModel.deleted_at.is_(None),
            )
            .first()
            is not None
        )

        return {
            "id": post.id,
            "text_content": post.text_content,
            "media_url": post.media_url,
            "media_type": post.media_type,
            "thumbnail_url": post.thumbnail_url,
            "created_at": post.created_at,
            "user_id": post.user_id,
            "likes_count": post.likes_count or 0,
            "dislikes_count": post.dislikes_count or 0,
            "shares_count": post.shares_count or 0,
            "views_count": post.views_count or 0,
            "comments_count": post.comments_count or 0,
            "has_liked": has_liked,
            "author": {
                "id": post.author.id,
                "firstname": post.author.firstname,
                "lastname": post.author.lastname,
                "profile_image_url": post.author.profile_image_url or "",
            },
            "feeling": post.feeling,
            "activity": post.activity,
            "checkin_place": post.checkin_place,
            "checkin_metadata": post.checkin_metadata,
            "tagged_friends": [
                {"id": tagged.id, "user_id": tagged.user_id}
                for tagged in post.tagged_friends
            ],
        }
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to fetch post_id=%s for user_id=%s",
            post_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch post.",
        ) from None


def get_posts_feed_controller(
    limit: int,
    offset: int,
    db: Session,
    current_user_id: int
) -> list[dict]:
    """Return original posts and reposts in chronological feed order."""
    total_likes_subq = (
        db.query(
            PostLikeModel.post_id,
            func.count(PostLikeModel.id).label("total_likes")
        )
        .filter(PostLikeModel.deleted_at.is_(None))  
        .group_by(PostLikeModel.post_id)
        .subquery()
    )

    user_liked_posts_subq = (
        db.query(PostLikeModel.post_id)
        .filter(
            PostLikeModel.user_id == current_user_id,
            PostLikeModel.deleted_at.is_(None)       
        )
        .subquery()
    )

    original_entries = (
        db.query(
            PostModel.id.label("post_id"),
            PostModel.created_at.label("feed_created_at"),
            literal(0).label("is_repost"),
            literal(None, type_=PostRepostModel.id.type).label("repost_id"),
            literal(None, type_=UserModel.id.type).label("reposter_id"),
            literal("anyone").label("visibility"),
        )
        .filter(
            PostModel.is_deleted == False,
            PostModel.author_id.is_not(None),
            PostModel.moderation_status == "approved",
        )
    )
    repost_entries = (
        db.query(
            PostRepostModel.post_id.label("post_id"),
            PostRepostModel.created_at.label("feed_created_at"),
            literal(1).label("is_repost"),
            PostRepostModel.id.label("repost_id"),
            PostRepostModel.user_id.label("reposter_id"),
            PostRepostModel.visibility.label("visibility"),
        )
        .join(PostModel, PostModel.id == PostRepostModel.post_id)
        .filter(
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
    reposter = aliased(UserModel)

    query = (
        db.query(
            PostModel,
            feed_entries.c.feed_created_at,
            feed_entries.c.is_repost,
            feed_entries.c.repost_id,
            feed_entries.c.visibility,
            reposter,
            func.coalesce(total_likes_subq.c.total_likes, 0).label("like_count"),
            case(
                (user_liked_posts_subq.c.post_id.is_not(None), 1),
                else_=0
            ).label("has_liked")
        )
        .join(feed_entries, PostModel.id == feed_entries.c.post_id)
        .options(joinedload(PostModel.author), selectinload(PostModel.tagged_friends))
        .outerjoin(total_likes_subq, PostModel.id == total_likes_subq.c.post_id)
        .outerjoin(user_liked_posts_subq, PostModel.id == user_liked_posts_subq.c.post_id)
        .outerjoin(reposter, reposter.id == feed_entries.c.reposter_id)
    )

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

    query = query.filter(
        or_(
            feed_entries.c.is_repost == 0,
            ~db.query(BlockList.id)
            .filter(
                BlockList.blocker_id == current_user_id,
                BlockList.blocked_id == feed_entries.c.reposter_id,
            )
            .exists(),
        ),
        or_(
            feed_entries.c.is_repost == 0,
            ~db.query(BlockList.id)
            .filter(
                BlockList.blocker_id == feed_entries.c.reposter_id,
                BlockList.blocked_id == current_user_id,
            )
            .exists(),
        ),
    )

    results = (
        query.order_by(
            feed_entries.c.feed_created_at.desc(),
            feed_entries.c.is_repost.desc(),
            PostModel.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    feed = []
    for (
        post,
        feed_created_at,
        is_repost,
        repost_id,
        visibility,
        reposted_by,
        like_count,
        has_liked,
    ) in results:
        if not post.author:
            continue

        is_repost = bool(is_repost)
        feed.append({
            "id": post.id,
            "feed_item_id": f"repost:{repost_id}" if is_repost else f"post:{post.id}",
            "user_id": post.user_id,
            "text_content": post.text_content,
            "media_url": post.media_url,
            "media_type": post.media_type,
            "thumbnail_url": post.thumbnail_url,
            "created_at": post.created_at,
            "feed_created_at": feed_created_at,
            "is_repost": is_repost,
            "visibility": visibility,
            "reposted_at": feed_created_at if is_repost else None,
            "reposted_by": {
                "id": reposted_by.id,
                "firstname": reposted_by.firstname,
                "lastname": reposted_by.lastname,
                "profile_image_url": reposted_by.profile_image_url or "",
            } if is_repost and reposted_by else None,
            "likes_count": like_count,
            "dislikes_count": post.dislikes_count or 0,
            "shares_count": post.shares_count or 0,
            "views_count": post.views_count or 0,
            "has_liked": bool(has_liked),
            "author": {
                "id": post.author.id,  
                "firstname": getattr(post.author, "firstname", "Unknown"),
                "lastname": getattr(post.author, "lastname", "User"),
                "profile_image_url": post.author.profile_image_url or "",
            },
            "feeling": post.feeling,
            "activity": post.activity,
            "checkin_place": post.checkin_place,
            "checkin_metadata": post.checkin_metadata,
            "tagged_friends": [
                {"id": tagged.id, "user_id": tagged.user_id}
                for tagged in post.tagged_friends
            ],
        })

    return feed
