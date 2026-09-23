from fastapi import FastAPI, Depends, HTTPException, APIRouter,status
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.User.Schema.Userregistraion_Schema import UserCreate, UserResponse
from src.User.Controller.register_controller import register_user as register_user_controller

user_router = APIRouter(prefix="/user")

@user_router.post(
    "/register_user", 
    response_model=UserResponse, 
    # 🟢 THE MASTER PLUG: Hard-blocks these specific plain-text strings from entering the network response!
    response_model_exclude={"password", "confirmpassword"}, 
    status_code=status.HTTP_201_CREATED
)

async def register_user(body: UserCreate, db: Session = Depends(init_db)):
    
    return await register_user_controller(body, db)


