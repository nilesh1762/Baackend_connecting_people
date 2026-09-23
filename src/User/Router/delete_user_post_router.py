from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status, APIRouter
from sqlalchemy.orm import Session
from src.User.model import FriendRequest, RequestStatus, Friendship,UserModel
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from src.User.Controller.delete_media_storage_controller import clean_up_media_storage
from src.User.model import UserModel, PostModel

user_router = APIRouter(prefix="/user")

@user_router.delete("/post_delete/{post_id}", status_code=status.HTTP_200_OK)
async def delete_user_post(
    post_id: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(init_db)
):
    # Find the active post entry in the database
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post data record not found.")

    # Save target file references before altering the database record
    media_to_delete = post.media_url
    thumbnail_to_delete = post.thumbnail_url

    # A. SOFT DELETE: Update flags instantly so it disappears from feed queries
    post.is_deleted = True 
    db.commit()

    # B. HARD DELETE STORAGE: Add file cleanup to async background execution thread
    if media_to_delete:
        background_tasks.add_task(
            clean_up_media_storage, 
            media_to_delete, 
            thumbnail_to_delete
        )

    return {"detail": "Post successfully deleted."}