from datetime import datetime, timezone
import redis
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.User.Service.auth_service import get_valid_token_payload, blacklist_token
from src.utils.setting import get_settings

settings = get_settings()
# Standard Bearer token extractor scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

user_router = APIRouter(prefix="/user" , tags=["Authentication"])

@user_router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(token: str = Depends(oauth2_scheme)):
    """
    Safely handles token extraction and passes it to the blacklist engine 
    even if the token signature is already expired.
    """
    try:
        # 🔴 THE CRITICAL BACKEND FIX:
        # options={"verify_exp": False} tells PyJWT to decode the token's structural payload
        # without crashing if it has expired. This guarantees your API returns a 200 OK.
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False} 
        )
        
        # Package the data structure to match what your blacklist_token service expects
        token_data = {"token": token, "payload": payload}
        
        # Trigger your independent business logic layer to push data into Redis cache storage
        blacklist_token(token_data)
            
        return {"status": "success", "message": "Successfully logged out"}
        
    except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError):
        # Fallback security valve: If the token is completely malformed or corrupted text, reject it
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed or invalid authentication token string structure configuration."
        )
