from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.User.Controller.PostController.content_moderation_controller import (
    get_pending_post_media_controller,
    moderate_post_media_controller,
)
from src.utils.content_moderation import require_content_moderator
from src.utils.db import init_db
from src.utils.security import get_current_user_id

router = APIRouter(prefix="/user/moderation", tags=["Content Moderation"])


@router.get("/posts/pending", status_code=status.HTTP_200_OK)
def get_pending_post_media(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db),
):
    require_content_moderator(current_user_id)
    return get_pending_post_media_controller(db=db, limit=limit, offset=offset)


@router.post("/posts/{post_id}/approve", status_code=status.HTTP_200_OK)
def approve_post_media(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db),
):
    require_content_moderator(current_user_id)
    return moderate_post_media_controller(
        db=db,
        post_id=post_id,
        decision="approved",
    )


@router.post("/posts/{post_id}/reject", status_code=status.HTTP_200_OK)
def reject_post_media(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db),
):
    require_content_moderator(current_user_id)
    return moderate_post_media_controller(
        db=db,
        post_id=post_id,
        decision="rejected",
    )
