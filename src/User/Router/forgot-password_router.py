from fastapi import FastAPI, Depends, HTTPException, APIRouter,status,Request
from sqlalchemy.orm import Session

from src.utils.db import init_db
from pydantic import BaseModel, EmailStr
from src.User.model import UserModel, PasswordResetToken, ForgotPasswordRequest,ResetPasswordSubmit
from fastapi import BackgroundTasks
import secrets
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import hashlib
from src.utils.email import send_email
from sqlalchemy.sql import func, literal
import bcrypt

user_router = APIRouter(prefix="/user")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@user_router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(init_db)):
    user = db.query(UserModel).filter(UserModel.email == payload.email.lower()).first()
   
      # Secure Architecture: Don't reveal if user doesn't exist
    if not user:
        return {"message": "If the email exists, a reset link has been issued."}
    
    user_email_str = str(user.email)
    user_id_int = user.id

    raw_token = secrets.token_urlsafe(32)
    expiration = datetime.utcnow() + timedelta(minutes=15)
    token_hash_to_save = hashlib.sha256(raw_token.encode()).hexdigest()
    # # Securely store hashed token to protect database leak threats
    # user.reset_token = pwd_context.hash(raw_token)
    # user.token_expires = expiration

    try:
        # Clean out old unexpired token requests
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id_int).delete()

        # Insert new token tracking item
        token_record = PasswordResetToken(
            user_id=user_id_int,
            token_hash=token_hash_to_save,
            expires_at=expiration
        )
        db.add(token_record)
        db.commit() 

    except Exception as db_err:
        db.rollback()
        print(f"Database Error: {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal processing error."
        )
   
    background_tasks.add_task(send_email, [user_email_str], raw_token)
    return {"message": "If the email exists, a reset link has been issued."}

@user_router.post("/reset-password")
def reset_password(
    payload: ResetPasswordSubmit, 
    db: Session = Depends(init_db)
):
    # Hash incoming token to search database securely
    incoming_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    
    token_record_query = db.query(PasswordResetToken).filter(
        func.trim(func.lower(PasswordResetToken.token_hash)) == incoming_hash.lower().strip(),
        PasswordResetToken.is_used == 0
    ).limit(1)

    token_record = token_record_query.one_or_none()
    
    # 🌟  Check if token exists first to prevent 'NoneType' crashes
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The verification link is invalid or has expired.1"
        )
        
    # 🌟 Safely parse expiration now that we know token_record is real
    # db_expires_naive = token_record.expires_at.replace(tzinfo=None)
    # current_time_naive = datetime.now().replace(tzinfo=None)
    db_expires_naive = token_record.expires_at.replace(tzinfo=None)
    current_time_naive = datetime.utcnow()
    
    
    # Check expiration timing
    if db_expires_naive < current_time_naive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The verification link is invalid or has expired.2"
        )
        
    # Fetch targeted user record associated with token context
    user = db.query(UserModel).filter(UserModel.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Update credentials securely (Remember to hash your new password using Passlib/Bcrypt!)
    # user.hashed_password = payload.new_password  # Placeholder mapping
    
    new_password_bytes = payload.new_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(new_password_bytes, salt)

    print("USER--", user._password_hash, hashed_password_bytes.decode('utf-8'))
# Convert bytes to string before saving to Oracle (if your column expects a string)
    user._password_hash = hashed_password_bytes.decode('utf-8') 
    # Mark token row used immediately to eliminate repeat execution hazards
    token_record.is_used = 1
    
    db.commit()
    return {"detail": "Password has been updated successfully. You can now log in with your new password."}
        

   
    