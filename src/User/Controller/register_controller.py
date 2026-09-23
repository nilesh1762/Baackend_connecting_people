from src.User.Schema.Userregistraion_Schema import UserCreate
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import bcrypt
from src.User.model import UserModel
from datetime import date, datetime
from sqlalchemy.sql import func  # Added func
from src.utils.email import send_email

from src.utils.security import create_email_verification_token
from src.utils.send_verification_email import send_verification_email

DEFAULT_THEME_VIDEOS = {
    "READING": "https://cloudinary.com",
    "BUSINESS": "https://cloudinary.com",
    "ART": "https://cloudinary.com",
    "NEIGHBORHOOD": "https://cloudinary.com"
}
DEFAULT_AVATAR_PLACEHOLDER = "https://cloudinary.com"

async def register_user(body: UserCreate, db: Session):
    user_data = body.model_dump()
    print("Inside register_user controller with data:", user_data)

    # 1. Pop out the dictionary structure
    dob_dict = user_data.pop("dateofbirth")
    db_date = date(
        year=int(dob_dict["birthYear"]),
        month=int(dob_dict["birthMonth"]),
        day=int(dob_dict["birthDay"])
    )
    # print("Inside register_user controller with data:", db_date)

    #Check if the email already exists in the database
    existing_user = db.query(UserModel).filter(UserModel.email == body.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

     # 2. Extract their simple favorite interest to match the video backdrop theme loop
    normalized_interest = body.my_interest.upper()
    assigned_video_cover = DEFAULT_THEME_VIDEOS.get(normalized_interest, DEFAULT_THEME_VIDEOS["READING"])

    
    # Hash the password before storing it
    hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create a new user instance
    new_user = UserModel(
        firstname=body.firstname,
        lastname=body.lastname,
        dateofbirth=db_date,
        gender=body.gender,
        email=body.email,
        mobilenumber=body.mobilenumber,
        country=body.country,
        _password_hash=hashed_password.decode('utf-8'),  # Store the hashed password    
        created_at=datetime.now(),
        main_focus=user_data.get("main_focus", "PURPOSE").upper(),
        current_feeling=user_data.get("current_feeling", "PEACEFUL").upper(),
        my_interest=normalized_interest,
        biggest_wish=user_data.get("biggest_wish", "MIND_PEACE").upper(),
        cover_video_url=assigned_video_cover,
        cover_image_url=None, 
        profile_image_url=DEFAULT_AVATAR_PLACEHOLDER
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
   

 # FIX: Add .decode('utf-8') to force Python to save it as text, not a bytes object!
    verification_token = create_email_verification_token(new_user.id).decode('utf-8')  
    
    # Compile the clean URL link string
    account_verification_link = f"http://localhost:8000/user/verify?token={verification_token}"
    # CALL THE UPDATED UTILITY ASYNC WORKFLOW HERE:
    try:
        await send_verification_email(
            email=new_user.email,
            activation_link=account_verification_link,
            firstname=new_user.firstname
        )
    except Exception as email_err:
        print(f"Background Delivery Issue: {email_err}")
      
    return new_user 