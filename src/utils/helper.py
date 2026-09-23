import jwt
from src.User.model import UserModel
from fastapi import Depends, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from src.utils.db import init_db
from src.utils.setting import get_settings

settings = get_settings()

def is_authenticated(request: Request, db: Session = Depends(init_db)):

 try:
    token = request.headers.get("Authorization")
   
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing")
    
    token = token.split(" ")[1] if token and " " in token else None
    
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    user_email = data.get("email")
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")   
    
    user = db.query(UserModel).filter(UserModel.email == user_email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
   
    return user

 except jwt.InvalidTokenError:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authorized to access this resource. Please log in again.")   