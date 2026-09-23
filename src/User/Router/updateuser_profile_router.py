from fastapi import FastAPI, Depends, HTTPException, APIRouter,status
from sqlalchemy.orm import Session
from src.User.model import UpdateUserProfile
from src.User.Controller.Userupdate_controller import update_profile_controller
from src.utils.db import init_db
from src.User.Schema.Userregistraion_Schema import UserCreate, UserResponse
from src.User.Controller.register_controller import register_user as register_user_controller
from src.utils.security import get_current_user_id

user_router = APIRouter(prefix="/user")

@user_router.put("/update_profile",response_model=UserResponse, status_code=status.HTTP_200_OK)

async def update_profile(
     body: UpdateUserProfile, 
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
   
    return await update_profile_controller(
         body=body, 
        db=db, 
        current_user_id=current_user_id
    )


