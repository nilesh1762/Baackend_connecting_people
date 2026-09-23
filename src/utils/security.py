import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.utils.setting import get_settings
from datetime import datetime, timedelta, timezone
# 1. This tells FastAPI to look for a 'Bearer <token>' string in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    
    """
    Extracts the JWT token from the header, decodes it using the app's secret key,
    and returns the unique user ID integer.
    """
    settings = get_settings()
   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 2. Decode the token using your environment variables
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 3. Extract the user ID (often stored under the 'sub' key in JWT claims)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        return int(user_id)
        
    except (jwt.PyJWTError, ValueError):
        # Catches expired tokens, wrong keys, or invalid integer values
        raise credentials_exception

def create_email_verification_token(user_id: int) -> str:
    """Generates a secure, isolated short-lived JWT token for email verification links."""
    settings = get_settings()
    
    payload = {
        "sub": str(user_id),               # Uses standard 'sub' key matching your parser layout
        "purpose": "email_verification",   # Explicitly flagged so it cannot be used for standard logins
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15) # Standard 15-minute activation lifespan
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)