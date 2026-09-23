from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import FriendRequest, RequestStatus, Friendship,UserModel
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from src.User.Controller.reject_friend_request_controller import reject_friend_request_controller
user_router = APIRouter(prefix="/user")

@user_router.post("/friends/request/{request_id}/reject", status_code=status.HTTP_200_OK)
def reject_friend_request(
    request_id: int, 
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """FastAPI endpoint that triggers the friend request rejection controller."""
    return reject_friend_request_controller(
        request_id=request_id, 
        current_user_id=current_user_id, 
        db=db
    )