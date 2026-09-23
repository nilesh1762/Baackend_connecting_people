import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import UserModel
from src.utils.setting import get_settings

async def verify_stateless_token_controller(token: str, db: Session):
    settings = get_settings()
    invalid_link_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The verification link is invalid or has expired."
    )
    
    # 🌟 CRUCIAL STEP: Fix URL space character encoding corruption 
    # This automatically safely replaces blank spaces back into standard plus signs (+)
    clean_token = token.replace(" ", "+")
    
    try:
        # Decode using your clean string parameter format
        payload = jwt.decode(clean_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("purpose") != "email_verification":
            print("Token Validation Error: Mismatched purpose string parameter.")
            raise invalid_link_exception
            
        user_id = payload.get("sub")
        if not user_id:
            print("Token Validation Error: Missing 'sub' user payload key anchor.")
            raise invalid_link_exception
            
        user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")
            
        if user.is_active:
            return {"message": "Account is already verified and active."}
            
        user.is_active = True
        db.commit()
        db.refresh(user)
        
        return {"message": "Email verified successfully! Your account is now active."}
        
    except Exception as raw_error:
        # 🌟 THIS PRINT STATEMENT WILL FORCE YOUR LOGS TO REVEAL THE TRUE BUG SYSTEM LOG:
        print("\n" + "="*50)
        print(f"🚨 CRITICAL TOKEN DEBUG LOG: Decode failed.")
        print(f"Error Type: {type(raw_error).__name__}")
        print(f"True Internal Message: {raw_error}")
        print("="*50 + "\n")
        raise invalid_link_exception
