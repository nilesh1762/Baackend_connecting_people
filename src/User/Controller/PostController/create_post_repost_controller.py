import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.User.model import (
    BlockList,
    Friendship,
    PostModel,
    PostRepostModel,
    UserModel,
)

logger = logging.getLogger(__name__)


def create_post_repost_controller(
    db: Session,
    current_user_id: int,
    post_id: int,
    visibility: str = "anyone",
) -> dict[str, Any]:
    """Create one idempotent repost entry for the current user and original post."""
    try:
        if visibility not in {"anyone", "friends"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visibility must be 'anyone' or 'friends'.",
            )

        post = (
            db.query(PostModel)
            .filter(
                PostModel.id == post_id,
                PostModel.is_deleted == False,
                PostModel.author_id.is_not(None),
                PostModel.moderation_status == "approved",
            )
            .with_for_update()
            .first()
        )
        if post is None or post.author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found.",
            )

        user = (
            db.query(UserModel)
            .filter(UserModel.id == current_user_id)
            .first()
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        if post.author_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot repost your own post.",
            )

        blocked_relationship = (
            db.query(BlockList.id)
            .filter(
                (
                    (BlockList.blocker_id == current_user_id)
                    & (BlockList.blocked_id == post.author_id)
                )
                | (
                    (BlockList.blocker_id == post.author_id)
                    & (BlockList.blocked_id == current_user_id)
                )
            )
            .first()
        )
        if blocked_relationship is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found.",
            )

        repost = (
            db.query(PostRepostModel)
            .filter(
                PostRepostModel.user_id == current_user_id,
                PostRepostModel.post_id == post_id,
            )
            .first()
        )
        duplicate_request = repost is not None
        if repost is None:
            repost = PostRepostModel(
                user_id=current_user_id,
                post_id=post_id,
                visibility=visibility,
            )
            db.add(repost)
            db.flush()
            db.refresh(repost)

        response = {
            "message": "Post reposted." if not duplicate_request else "Post already reposted.",
            "post_id": post_id,
            "repost_id": repost.id,
            "is_repost": True,
            "visibility": repost.visibility,
            "duplicate_request": duplicate_request,
            "created_at": repost.created_at,
            "reposted_by": {
                "id": user.id,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "profile_image_url": user.profile_image_url or "",
            },
        }
        db.commit()
        return response
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to create repost for post_id=%s and user_id=%s",
            post_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to repost post.",
        ) from None


def delete_post_repost_controller(
    db: Session,
    current_user_id: int,
    post_id: int,
) -> dict[str, Any]:
    """Remove the current user's repost; repeating the request is safe."""
    try:
        repost = (
            db.query(PostRepostModel)
            .filter(
                PostRepostModel.user_id == current_user_id,
                PostRepostModel.post_id == post_id,
            )
            .with_for_update()
            .first()
        )
        was_reposted = repost is not None
        if repost is not None:
            db.delete(repost)
            db.flush()

        db.commit()
        return {
            "message": "Repost removed." if was_reposted else "Post was not reposted.",
            "post_id": post_id,
            "repost_id": None,
            "is_repost": False,
            "duplicate_request": not was_reposted,
            "created_at": None,
            "reposted_by": None,
        }
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Failed to remove repost for post_id=%s and user_id=%s",
            post_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to undo repost.",
        ) from None
