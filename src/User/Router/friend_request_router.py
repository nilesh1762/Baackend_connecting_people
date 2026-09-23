from fastapi import APIRouter, FastAPI, Depends, HTTPException, status

from sqlalchemy.orm import Session

from src.User.model import FriendRequest, RequestStatus, Friendship,UserModel
from src.User.Schema.Friendrequest_Schema import FriendRequestCreate
from src.User.Schema.Friendrequest_Schema import FriendRequestResponse
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from src.User.Controller.send_friend_request_controller import send_friend_request_controller

user_router = APIRouter(prefix="/user")

@user_router.post("/friends/request", status_code=status.HTTP_201_CREATED)
def send_friend_request(
    schema: FriendRequestCreate, 
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """FastAPI endpoint that triggers the friend request controller."""
    return send_friend_request_controller(
        receiver_id=schema.receiver_id, 
        current_user_id=current_user_id, 
        db=db
    )