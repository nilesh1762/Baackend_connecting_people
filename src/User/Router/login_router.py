from fastapi import FastAPI, Depends, HTTPException, APIRouter,status,Request
from sqlalchemy.orm import Session
from src.User.Schema.Userregistraion_Schema import AuthUser, UserResponse
from src.User.Controller.login_controller import login_user, is_authenticated
from src.User.Schema.Userlogin_Schema import LoginRequest
from src.utils.db import init_db


user_router = APIRouter(prefix="/user")

@user_router.post("/login_user", status_code=status.HTTP_201_CREATED)

def user_login(body: LoginRequest, db: Session = Depends(init_db)):
    return login_user(body, db)


@user_router.get("/is_auth", status_code=status.HTTP_201_CREATED, response_model=AuthUser)

def get_token(request: Request, db: Session = Depends(init_db)):
    return is_authenticated(request.headers.get("Authorization"), db)
 