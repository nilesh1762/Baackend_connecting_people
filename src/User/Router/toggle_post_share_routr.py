from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

# 🚀 IMPORT LOCAL SECTIONS FROM YOUR BACKEND FILES
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.log_post_share_controller import log_post_share_controller


user_router = APIRouter(prefix="/user", tags=["Post Metrics"])
# ========================================================
# 🚀 THE SHARE ENDPOINT (Protected by user authentication)
# ========================================================
@user_router.post("/{post_id}/share", status_code=status.HTTP_200_OK)
async def toggle_post_share(
    post_id: int,
    platform: str = Query(default="internal", description="Target platform: internal, twitter, whatsapp"),
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Handles Twitter-style single-share toggling for a post. 
    Logs user details and manages the share count securely.
    """
    return log_post_share_controller(
        db=db, 
        current_user_id=current_user_id, 
        post_id=post_id, 
        platform=platform
    )
