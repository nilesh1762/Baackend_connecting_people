import logging

from fastapi import HTTPException, status

from src.utils.setting import get_settings

logger = logging.getLogger(__name__)


def require_content_moderator(current_user_id: int) -> None:
    configured_ids = get_settings().CONTENT_MODERATOR_USER_IDS
    try:
        moderator_ids = {
            int(user_id.strip())
            for user_id in configured_ids.split(",")
            if user_id.strip()
        }
    except ValueError:
        logger.exception("CONTENT_MODERATOR_USER_IDS contains a non-integer value")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content moderation is misconfigured.",
        ) from None

    if not moderator_ids:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No content moderators are configured.",
        )
    if current_user_id not in moderator_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to moderate content.",
        )
