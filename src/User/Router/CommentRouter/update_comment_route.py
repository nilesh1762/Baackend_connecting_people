from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from src.User.Controller.CommentController.update_comment_controller import (
    update_comment_controller,
)
from src.utils.db import init_db
from src.utils.security import get_current_user_id

user_router = APIRouter(prefix="/user", tags=["Comments"])


@user_router.patch(
    "/comments/{comment_id}",
    status_code=status.HTTP_200_OK,
)
def update_comment(
    comment_id: int,
    text_content: Optional[str] = Form(None),
    attached_gif_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    clear_media: bool = Form(False),
    clear_gif: bool = Form(False),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db),
):
    return update_comment_controller(
        comment_id=comment_id,
        current_user_id=current_user_id,
        db=db,
        text_content=text_content,
        attached_gif_url=attached_gif_url,
        file=file,
        clear_media=clear_media,
        clear_gif=clear_gif,
    )
