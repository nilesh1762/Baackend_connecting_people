import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from sqlalchemy.orm import Session
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.create_post_controller import create_post_controller
from src.User.Schema.post_summary_Schema import PostResponse
from typing import Optional, Any
from src.User.model import PostModel

user_router = APIRouter(prefix="/user", tags=["Content Delivery"])

@user_router.post("/post/summary", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_new_feed_post(
    text_content: Optional[str] = Form(None),
    feeling: Optional[str] = Form(None),
    activity: Optional[str] = Form(None),
    checkin_json: Optional[str] = Form(None),       
    tagged_friends_json: Optional[str] = Form(None),  
    
    # ✅ 2. Wrap the binary stream variable explicitly in File(None)
    file: Optional[UploadFile] = File(None),
    
    # ✅ 3. CRITICAL FIX: Wrap your structural session dependencies inside Depends()
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id)
) -> Any:
    """Multipart form endpoint processing post creations for text, images, animated GIFs, or streaming videos with interactive social tag parameters."""
    
    # 🚀 Pass all the fields cleanly directly down to your controller function
    return create_post_controller(
        text_content=text_content,
        file=file,
        feeling=feeling,
        activity=activity,
        checkin_json=checkin_json,
        tagged_friends_json=tagged_friends_json,
        db=db,
        current_user_id=current_user_id
    )
