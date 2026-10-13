import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.User.model import (
    BlockList,
    PostModel,
    PostShareModel,
    PostShareRecipientModel,
    UserModel,
)

logger = logging.getLogger(__name__)


def log_post_share_controller(
    db: Session,
    current_user_id: int,
    post_id: int,
    platform: str = "internal",
    idempotency_key: Optional[str] = None,
    recipient_ids: Optional[list[int]] = None,
) -> Dict[str, Any]:
    """Record a share event and optionally deliver it to users' in-app inboxes."""
    try:
        recipient_ids = list(dict.fromkeys(recipient_ids or []))
        post = (
            db.query(PostModel)
            .filter(
                PostModel.id == post_id,
                PostModel.is_deleted == False,
                PostModel.moderation_status == "approved",
            )
            .with_for_update()
            .first()
        )
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target post not found.",
            )

        current_user = (
            db.query(UserModel)
            .filter(UserModel.id == current_user_id)
            .first()
        )
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if current_user_id in recipient_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot share a post with yourself.",
            )

        if recipient_ids:
            existing_recipients = {
                user_id
                for (user_id,) in db.query(UserModel.id)
                .filter(UserModel.id.in_(recipient_ids))
                .all()
            }
            missing_recipients = sorted(set(recipient_ids) - existing_recipients)
            if missing_recipients:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more share recipients were not found.",
                )

            blocked_recipient = (
                db.query(BlockList.id)
                .filter(
                    (
                        (BlockList.blocker_id == current_user_id)
                        & (BlockList.blocked_id.in_(recipient_ids))
                    )
                    | (
                        (BlockList.blocker_id.in_(recipient_ids))
                        & (BlockList.blocked_id == current_user_id)
                    )
                )
                .first()
            )
            if blocked_recipient:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot share a post with a user who is blocked.",
                )

        existing_event = None
        if idempotency_key is not None:
            existing_event = (
                db.query(PostShareModel)
                .filter(
                    PostShareModel.user_id == current_user_id,
                    PostShareModel.idempotency_key == idempotency_key,
                )
                .first()
            )
            if existing_event is not None and existing_event.post_id != post_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency-Key was already used for a different post.",
                )
            if existing_event is not None:
                existing_recipient_ids = {
                    recipient.recipient_id
                    for recipient in existing_event.recipients
                }
                if (
                    existing_event.platform_target != platform
                    or existing_recipient_ids != set(recipient_ids)
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Idempotency-Key was reused with different share details.",
                    )

        if existing_event is None:
            share_event = PostShareModel(
                user_id=current_user_id,
                post_id=post_id,
                platform_target=platform,
                idempotency_key=idempotency_key,
            )
            db.add(share_event)
            db.flush()
            db.add_all(
                PostShareRecipientModel(
                    share_id=share_event.id,
                    recipient_id=recipient_id,
                )
                for recipient_id in recipient_ids
            )
        else:
            share_event = existing_event

        shares_count = (
            db.query(func.count(PostShareModel.id))
            .filter(PostShareModel.post_id == post_id)
            .scalar()
            or 0
        )
        post.shares_count = shares_count
        response = {
            "message": "Post share recorded.",
            "post_id": post_id,
            "share_id": share_event.id,
            "shares_count": shares_count,
            "share_recorded": True,
            "duplicate_request": existing_event is not None,
            "recipient_ids": recipient_ids,
            "user_details": {
                "id": current_user.id,
                "firstname": current_user.firstname,
                "lastname": current_user.lastname,
                "profile_image_url": current_user.profile_image_url or "",
            },
        }
        db.commit()

        return response
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to record share for post_id=%s and user_id=%s",
            post_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to record post share.",
        ) from None


def get_received_post_shares_controller(
    db: Session,
    current_user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return non-deleted posts shared directly with the current user."""
    try:
        rows = (
            db.query(
                PostShareRecipientModel,
                PostShareModel,
                PostModel,
                UserModel,
            )
            .join(
                PostShareModel,
                PostShareRecipientModel.share_id == PostShareModel.id,
            )
            .join(PostModel, PostShareModel.post_id == PostModel.id)
            .join(UserModel, PostShareModel.user_id == UserModel.id)
            .filter(
                PostShareRecipientModel.recipient_id == current_user_id,
                PostModel.is_deleted == False,
                PostModel.moderation_status == "approved",
            )
            .order_by(PostShareModel.created_at.desc(), PostShareModel.id.desc())
            .offset(offset)
            .limit(limit + 1)
            .all()
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to load shared posts for user_id=%s",
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load shared posts.",
        ) from None
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [
        {
            "share_id": share.id,
            "post_id": post.id,
            "platform": share.platform_target,
            "shared_at": share.created_at.isoformat() if share.created_at else None,
            "sender": {
                "id": sender.id,
                "firstname": sender.firstname,
                "lastname": sender.lastname,
                "profile_image_url": sender.profile_image_url or "",
            },
            "post": {
                "text_content": post.text_content,
                "media_url": post.media_url,
                "media_type": post.media_type,
                "thumbnail_url": post.thumbnail_url,
                "created_at": post.created_at.isoformat() if post.created_at else None,
            },
        }
        for _, share, post, sender in rows
    ]
    return {
        "items": items,
        "has_more": has_more,
        "next_offset": offset + len(items),
    }
