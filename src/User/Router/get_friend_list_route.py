from typing import List
from fastapi import  Depends, status, Query
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.User.Controller.get_friends_list_controller import get_friends_list_controller
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from src.User.Controller.send_friend_request_controller import send_friend_request_controller
from src.User.Schema.friend_list_Schema import FriendProfileResponse

user_router = APIRouter(prefix="/user")

@user_router.get("/friends/list", response_model=List[FriendProfileResponse], status_code=status.HTTP_200_OK)
def get_friends_list(
    limit: int = Query(default=10, ge=1, le=100, description="Number of friends to return per page"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """Retrieves a list of all active friends with profiles for the logged-in user."""
    return get_friends_list_controller(
        limit=limit,
        offset=offset,
        db=db,
        current_user_id=current_user_id
    )
 
