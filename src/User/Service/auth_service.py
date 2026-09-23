from datetime import datetime, timezone
import redis
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.utils.setting import get_settings

settings = get_settings()

# Centralized Redis connection instance
redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    decode_responses=True
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_valid_token_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency: Extracts, decodes, and verifies the incoming token against Redis.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid, expired, or logged-out token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Block request if token is in Redis blacklist
    if redis_client.exists(f"blacklist:{token}"):
        raise credentials_exception

    try:
        # 2. Decode the token signatures
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return {"token": token, "payload": payload}
        
    except (ExpiredSignatureError, InvalidTokenError):
        raise credentials_exception


def blacklist_token(token_data: dict) -> None:
    """
    Business Logic: Calculates token lifespan and pushes it to Redis.
    """
    token = token_data["token"]
    payload = token_data["payload"]
    
    exp_timestamp = payload.get("exp")
    if not exp_timestamp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token missing expiration properties."
        )
        
    # Calculate exact remaining life in seconds
    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    remaining_seconds = exp_timestamp - current_timestamp
    
    # Store token in Redis with a TTL countdown
    if remaining_seconds > 0:
        redis_client.setex(
            name=f"blacklist:{token}",
            time=remaining_seconds,
            value="true"
        )
