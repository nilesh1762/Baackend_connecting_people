from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.User.Schema.user_block_Schema import BlockActionRequest
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.block_user_controller import block_user_controller


user_router = APIRouter(prefix="/user", tags=["User Relationships"])
@user_router.post("/block", status_code=status.HTTP_200_OK)

def block_user(
    payload: BlockActionRequest, 
    db: Session = Depends(init_db), 
    current_user_id: int = Depends(get_current_user_id)
):
     """Processes relationship bans securely via controller orchestration."""
     return block_user_controller(
        target_id=payload.user_id_to_block,
        db=db,
        current_user_id=current_user_id
    )