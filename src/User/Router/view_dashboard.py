from fastapi import FastAPI, Depends, HTTPException, APIRouter,status,Request


from src.User.Controller.get_current_user import get_current_user
from src.utils.db import init_db
from src.User.model import UserModel

user_router = APIRouter(prefix="/user")
@user_router.get("/dashboard")

def view_dashboard(current_user: UserModel = Depends(get_current_user)):
    # This block is completely secure. If execution reaches here, 
    # the user is valid, verified, active, and fully authenticated.
    return {"message": f"Welcome back, {current_user.firstname}!"}
