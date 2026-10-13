from fastapi import APIRouter, Depends, status, Form, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.CommentController.create_rich_comment_controller import create_rich_comment_controller

user_router = APIRouter(prefix="/user", tags=["Content Delivery"])


def _comment_response(comment_record):
    return {
        "id": comment_record.id,
        "text": comment_record.text_content,
        "media_url": comment_record.media_url,
        "media_type": comment_record.media_type,
        "gif_url": comment_record.gif_url,
        "author_id": comment_record.author_id,
        "parent_comment_id": comment_record.parent_comment_id,
        "author_name": f"{comment_record.author.firstname} {comment_record.author.lastname}",
        "author_avatar": comment_record.author.profile_image_url,
        "created_at": comment_record.created_at.isoformat() if comment_record.created_at else None,
    }


@user_router.post("/{post_id}/rich-comment", status_code=status.HTTP_201_CREATED)
def submit_rich_comment(
    post_id: int,
    text_content: Optional[str] = Form(None),
    attached_gif_url: Optional[str] = Form(None),
    # 🌟 THE THREADED FIX: Accept an optional parent comment ID token field via incoming Form payload arrays
    parent_comment_id: Optional[int] = Form(None), 
    file: Optional[UploadFile] = File(None),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db)
):
    """💬 Post a rich multi-media comment or a nested sub-reply thread containing Text, Emojis, Device Photos, or Giphy URLs."""
    try:
        # Pass parent_comment_id straight down the wire into your core logic handler context block
        comment_record = create_rich_comment_controller(
            post_id=post_id,
            current_user_id=current_user_id,
            text_content=text_content,
            file=file,
            attached_gif_url=attached_gif_url,
            parent_comment_id=parent_comment_id, # 🌟 PASS IT DOWN HERE
            db=db
        )
        
        return _comment_response(comment_record)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Endpoint failed to process ingestion stack: {str(e)}"
        )


@user_router.post("/{post_id}/repost-comment", status_code=status.HTTP_201_CREATED)
def submit_repost_comment(
    post_id: int,
    text_content: Optional[str] = Form(None),
    attached_gif_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db),
):
    """Add a text, GIF, or image comment to the original post from a repost composer."""
    comment_record = create_rich_comment_controller(
        post_id=post_id,
        current_user_id=current_user_id,
        text_content=text_content,
        file=file,
        attached_gif_url=attached_gif_url,
        db=db,
        allow_video=False,
    )
    return _comment_response(comment_record)
