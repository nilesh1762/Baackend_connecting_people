from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from src.utils.db import init_db
from src.User.model import UserModel
from src.utils.setting import get_settings
# 1. Add Redis import
import redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()

# 2. Initialize your Redis connection client
# Update host/port matching your configuration settings if needed
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(init_db)):
    """
    FastAPI Security Dependency to authenticate a user via JWT.
    Automatically handles token extraction, expiration checks, and Redis blacklist validation.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not authorized to access this resource. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 3. 🔴 CRUCIAL LOGOUT CHECK: Intercept request before checking DB or decoding
    # If the token exists in Redis, it means the user manually logged out.
    if redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session ended. This token is no longer valid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    # 4. Optional: Return both user and token if your routes need the raw token for manual logout
    return user
