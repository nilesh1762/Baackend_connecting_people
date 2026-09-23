from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.User.Controller.verify_token_validate_controller import verify_stateless_token_controller

user_router = APIRouter(prefix="/user")

@user_router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_account(
    token: str = Query(..., description="The cryptographic verification token link"),
    db: Session = Depends(init_db)
):
    return await verify_stateless_token_controller(token=token, db=db)
