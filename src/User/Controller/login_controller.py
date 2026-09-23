
import jwt
from src.utils.setting import get_settings
from src.User.Schema.Userlogin_Schema import LoginRequest
from src.User.model import UserModel
from fastapi import HTTPException, status
import bcrypt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jwt import InvalidTokenError
from src.utils.accesstoken import create_access_token
from src.utils.decryptrsapassword import decrypt_rsa_password

# 1. Load system or .env variables via your settings utility
settings = get_settings()

def login_user(body: LoginRequest, db: Session):
    # Standard security exception setup
    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password", 
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Move decryption first so heavy work always runs before verification drops
        plain_password = decrypt_rsa_password(body.password)
    except Exception as e:
        print(f"Decryption failure event logged: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not securely process login payload."
        )

    # 1. Check if the user exists in the database
    user = db.query(UserModel).filter(UserModel.email == body.email).first()
    
    # Secure Timing Protection: If user doesn't exist, generate a fake hash 
    # to force bcrypt.checkpw to spend processing time anyway
    if user:
        database_hash = user._password_hash
    else:
        # A dummy bcrypt hash to consume server processing time uniformly
        database_hash = b"$2b$12$7kO9H8wE6rTYuIxPzA2bC.V9pXm5nL4sK3jR2qG1fE0dB9cA8v7uG"

    # Convert plaintext password securely to byte strings
    plain_password_bytes = plain_password.encode('utf-8')

    # Safely normalize hash into clean bytes dynamically
    if isinstance(database_hash, str):
        database_hash = database_hash.encode('utf-8')

    # 3. Verify the password bytes
    # If user didn't exist, this fails but consumes identical CPU cycles
    if not bcrypt.checkpw(plain_password_bytes, database_hash) or not user:
        raise invalid_credentials_exception

    # 4. Generate your JWT access token lifetime configuration
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),     
            "email": user.email
        }, 
        expires_delta=access_token_expires
    )

    # 5. Return complete session data structure matching your camelCase frontend expectations
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "firstName": getattr(user, "firstname", None) or user.email.split("@")[0], 
            "lastName": getattr(user, "lastname", None) or "",
        }
    }


def is_authenticated(token: str, db: Session):
  
  try:
    token = token.split(" ")[1] if token and " " in token else None
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing")
    
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    user_email = data.get("email")
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")   
    
    # exp_timestamp = data.get("exp")
    # if exp_timestamp is None:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")   
    
    # current_timestamp = datetime.now(timezone.utc).timestamp()
    # if current_timestamp > exp_timestamp:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authorized to access this resource. Please log in again.")
    
    #  # Check if the user exists in the database
    user = db.query(UserModel).filter(UserModel.email == user_email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
   
    return user

  except InvalidTokenError:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authorized to access this resource. Please log in again.")   
    
   