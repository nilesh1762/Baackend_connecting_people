from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.User.Controller.incoming_friend_requests_controller import get_incoming_friend_requests_controller as incoming_friend_requests_controller
from src.utils.db import init_db             # Adjust paths to your database session manager
from src.utils.security import get_current_user_id    # Adjust paths to your authentication helper

user_router = APIRouter(prefix="/user")
    
@user_router.get("/friends/requests/incoming", status_code=status.HTTP_200_OK)
def get_incoming_friend_requests(
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """
    FastAPI endpoint that aggregates all incoming pending friend requests 
    targeting the active logged-in account profile.
    """
    return incoming_friend_requests_controller(
        current_user_id=current_user_id, 
        db=db
    )
