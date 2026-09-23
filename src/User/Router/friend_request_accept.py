from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import FriendRequest, RequestStatus, Friendship,UserModel
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from src.User.Controller.accept_friend_request_controller import accept_friend_request_controller

user_router = APIRouter(prefix="/user")

@user_router.post("/friends/request/{request_id}/accept", status_code=status.HTTP_200_OK)


def accept_friend_request(
    request_id: int, 
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """FastAPI endpoint that triggers the friend request acceptance controller."""
    return accept_friend_request_controller(
        request_id=request_id, 
        current_user_id=current_user_id, 
        db=db
    )