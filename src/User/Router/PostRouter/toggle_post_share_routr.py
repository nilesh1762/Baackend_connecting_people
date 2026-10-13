from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.PostController.create_post_repost_controller import (
    create_post_repost_controller,
    delete_post_repost_controller,
)
from src.User.Controller.PostController.log_post_share_controller import (
    get_received_post_shares_controller,
    log_post_share_controller,
)
from src.User.Schema.share_post_schema import SharePostRequest
from src.User.Schema.post_repost_schema import RepostRequest

user_router = APIRouter(prefix="/user", tags=["Post Metrics"])


@user_router.post("/posts/{post_id}/repost", status_code=status.HTTP_201_CREATED)
def repost_post(
    post_id: int,
    response: Response,
    request: Optional[RepostRequest] = None,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Create a feed repost without recording a normal share event."""
    result = create_post_repost_controller(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
        visibility=request.visibility if request else "anyone",
    )
    if result["duplicate_request"]:
        response.status_code = status.HTTP_200_OK
    return result


@user_router.delete("/posts/{post_id}/repost", status_code=status.HTTP_200_OK)
def undo_repost(
    post_id: int,
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Remove the current user's repost without deleting the original post."""
    return delete_post_repost_controller(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
    )


@user_router.post("/{post_id}/share", status_code=status.HTTP_200_OK)
def share_post(
    post_id: int,
    request: Optional[SharePostRequest] = None,
    platform: str = Query(
        default="internal",
        min_length=1,
        max_length=100,
        description="Share destination, such as internal, whatsapp, or another platform.",
    ),
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
    idempotency_key: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
        description="Reuse the same key when retrying the same share request.",
    ),
):
    """Record a share action; repeating a request with the same key is idempotent."""
    return log_post_share_controller(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
        platform=platform,
        idempotency_key=idempotency_key,
        recipient_ids=request.recipient_ids if request else [],
    )


@user_router.get("/shared-with-me", status_code=status.HTTP_200_OK)
def get_shared_posts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """List posts that other users shared directly with the current user."""
    return get_received_post_shares_controller(
        db=db,
        current_user_id=current_user_id,
        limit=limit,
        offset=offset,
    )
