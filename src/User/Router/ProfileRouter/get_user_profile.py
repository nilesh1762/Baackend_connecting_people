from fastapi import APIRouter, Depends, status, HTTPException
from src.User.Schema.Userregistraion_Schema import UserCreate, UserResponse
from src.utils.security import get_current_user_id
from src.utils.db import init_db
from sqlalchemy.orm import Session
from src.User.model import UserModel


router = APIRouter(prefix="/user", tags=["Users"])

@router.get("/login_user_profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_profile(
    db: Session = Depends(init_db),
    current_user_id_val: int = Depends(get_current_user_id)
):
    """
    Fetches the profile information of the currently authenticated user.
    Forces the profile status to Online since the user is actively making the request.
    """
    user_profile = db.query(UserModel).filter(UserModel.id == current_user_id_val).first() 
    
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
        
    # 🟢 THE FIX: Force the profile status to True since this is the active user
    # This prevents the initial race condition layout flicker on login!
    user_profile.is_online = True
    
    # Optional fallback sync: If you want to check if they have an active socket open too
    # user_profile.is_online = current_user_id_val in presence_controller.active_connections or True

    return user_profile
