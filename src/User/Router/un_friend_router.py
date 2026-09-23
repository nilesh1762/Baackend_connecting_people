from fastapi import APIRouter, FastAPI, Depends, HTTPException, status

from sqlalchemy.orm import Session
from src.User.Controller.unfriend_user_controller import unfriend_user_controller
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from src.User.Controller.send_friend_request_controller import send_friend_request_controller

user_router = APIRouter(prefix="/user")

@user_router.delete("/friends/unfriend/{friend_id}", status_code=status.HTTP_200_OK)
def unfriend_user(
    friend_id: int, 
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    
    """Removes a friendship connection completely via controller orchestration."""
    return unfriend_user_controller(
        friend_id=friend_id,
        db=db,
        current_user_id=current_user_id
    )
