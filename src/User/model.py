from pydantic import field_serializer, BaseModel, EmailStr, Field, field_validator,model_validator
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Identity, Date, ForeignKey, Enum, UniqueConstraint, Text, Identity
from sqlalchemy.orm import relationship, declarative_base, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta, timezone
import enum
from typing import Optional, List


from src.utils.phone_validate import clean_and_validate_mobile
from src.utils.dob_validate import convert_date_to_dict, convert_dict_to_date

# Define India Standard Time Offset (+5:30)
IST_ZONE = timezone(timedelta(hours=5, minutes=30))
Base = declarative_base()


class UserEducationModel(Base):
    __tablename__ = "USER_EDUCATION_TABLE"

    id = Column("ID", Integer, Identity(start=1, increment=1), primary_key=True)
    user_id = Column("USER_ID", Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False)
    
    institution_name = Column("INSTITUTION_NAME", String(255), nullable=False)
    education_level = Column("EDUCATION_LEVEL", String(100), nullable=False)
    degree_title = Column("DEGREE_TITLE", String(255), nullable=True)
    specialization = Column("SPECIALIZATION", String(255), nullable=True)
    
    # 🟢 ENSURE BOTH DATE COLUMNS FORCE UPPERCASE STRINGS
    start_date = Column("START_DATE", Date, nullable=False)
    end_date = Column("END_DATE", Date, nullable=True) # 💥 FIXES THIS ERROR RIGHT HERE
    
    grade_or_gpa = Column("GRADE_OR_GPA", String(50), nullable=True) 
    
    user = relationship("UserModel", back_populates="education")


class UserModel(Base):
    __tablename__ = "USER_TABLE"
    
    id = Column("ID", Integer, Identity(start=1, increment=1), primary_key=True)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    
    # Internal physical database tracking column
    _dateofbirth = Column('dateofbirth', Date, nullable=False)
    
    gender = Column(String(20), nullable=False)
    email = Column(String(500), nullable=False, unique=True)
    mobilenumber =Column("MOBILENUMBER", String(20), nullable=False)
    localization = Column(String(100), nullable=False)
    bio = Column(String(1000), nullable=False)
    _password_hash = Column('password_hash', String(64), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now()) 

    main_focus = Column(String(50), name="MAIN_FOCUS", default="PURPOSE", nullable=False)
    current_feeling = Column(String(50), name="CURRENT_FEELING", default="PEACEFUL", nullable=False)
    my_interest = Column(String(50), name="MY_INTEREST", default="READING", nullable=False)
    biggest_wish = Column(String(50), name="BIGGEST_WISH", default="MIND_PEACE", nullable=False)



    profile_image_url = Column("PROFILE_IMAGE_URL", String(512), nullable=True)
    is_online = Column(Boolean, default=False, server_default="1", nullable=False)
    cover_image_url = Column(String(512), nullable=True)
    cover_video_url = Column(String(512), nullable=True)
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("PostModel", back_populates="author", foreign_keys="[PostModel.author_id]")
    city = Column("CITY", String(100), nullable=True, index=True)
    country = Column("COUNTRY", String(100), nullable=False, index=False)
    userrelationship = Column(String(50), nullable=True, default=None)
    website_url = Column(String(255), nullable=True, default=None)
    location_name = Column(String(100), nullable=True, default=None)
    profile_category = Column(String(100), nullable=True, default=None)
    shared_posts = relationship("PostShareModel", back_populates="shared_by_user", cascade="all, delete-orphan")
    education = relationship("UserEducationModel", back_populates="user", cascade="all, delete-orphan")
    status_presence = Column(String(20), default="offline", server_default="offline", nullable=False)
    #  The custom constructor to handle 'dateofbirth' correctly during initialization
    def __init__(self, **kwargs):
        dob = kwargs.pop("dateofbirth", None)
        super().__init__(**kwargs)
        if dob is not None:
            self.dateofbirth = dob

    # 2. Call the dictionary transformation utility here
    @hybrid_property
    def dateofbirth(self):
        return convert_date_to_dict(self._dateofbirth)

    # 3. Call the dictionary parsing utility here
    @dateofbirth.setter
    def dateofbirth(self, dob_dict):
        self._dateofbirth = convert_dict_to_date(dob_dict)

     
class PasswordResetToken(Base):
    __tablename__ = "PASSWORD_RESET_TOKENS"

    id = Column("ID", Integer, Identity(start=1, increment=1), primary_key=True)
    user_id = Column("USER_ID", Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False)
    token_hash = Column("TOKEN_HASH", String(64), unique=True, nullable=False)
    expires_at = Column("EXPIRES_AT", DateTime(timezone=True), nullable=False)
    is_used = Column("IS_USED", Integer, default=0, nullable=False) 
    created_at = Column("CREATED_AT", DateTime(timezone=True), server_default=func.now())

    user = relationship("UserModel", back_populates="reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, token_hash='{self.token_hash[:8]}...', is_used={self.is_used})>"
    

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class ResetPasswordSubmit(BaseModel):
    token: str = Field(..., description="The raw secure token received via email")
    # 1. Enforce minimum length of 8 characters for the new password
    new_password: str = Field(
        ..., 
        min_length=8, 
        description="The fresh secure password to save"
    )
    
    # 2. Add the confirm password field with the same length rule
    confirm_password: str = Field(
        ..., 
        min_length=8, 
        description="The confirmation password that must match new_password"
    )

    # 3. Add a model validator to ensure both fields are exactly identical
    @model_validator(mode='after')
    def verify_password_match(self) -> 'ResetPasswordSubmit':
        if self.new_password != self.confirm_password:
            raise ValueError("The new password and confirmation password do not match.")
        return self

    model_config = {
        "from_attributes": True
    } 

class UpdateEducationItem(BaseModel):
    id: Optional[int] = None # Optional so new records without IDs don't crash validation
    institution_name: str
    education_level: str
    degree_title: Optional[str] = None
    specialization: Optional[str] = None
    start_date: date         # Converts incoming strings like '2016-08-01' into date objects safely
    end_date: Optional[date] = None
    grade_or_gpa: Optional[str] = None

    class Config:
        from_attributes = True

class UpdateUserProfile(BaseModel):

    firstname: Optional[str] = Field(None, min_length=2, max_length=50)
    lastname: Optional[str] = Field(None, min_length=2, max_length=50)
    gender: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    mobilenumber: Optional[str] = Field(None)
    dateofbirth: Optional[dict] = Field(None)
    # Your brand new metadata field mappings
    localization: Optional[str] = Field(None, max_length=100)
    
    bio: Optional[str] = Field(None, max_length=1000)
    city: Optional[str] = None
    country: Optional[str] = None
    education: Optional[List[UpdateEducationItem]] = None
    userrelationship: Optional[str] = Field(None, max_length=50)
    website_url: Optional[str] = Field(None, max_length=255)
    location_name: Optional[str] = Field(None, max_length=100)
    profile_category: Optional[str] = Field(None, max_length=100)
    @field_validator('mobilenumber')
    @classmethod
    def validate_mobile(cls, value: str) -> str:
         return clean_and_validate_mobile(value)
    
    model_config = {
        "from_attributes": True
    }

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DELETED = "DELETED"

# 1. Friendship Request Tracker
class FriendRequest(Base):
    __tablename__ = "FRIEND_REQUESTS"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, index=True)
    receiver_id = Column(Integer, index=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Prevent duplicate records between the exact same two users
    __table_args__ = (UniqueConstraint('sender_id', 'receiver_id', name='_sender_receiver_uc'),)

# 2. Final Friendship Mapping Table
class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    friend_id = Column(Integer, index=True)
    created_at = Column(DateTime, server_default=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False) 

    # __table_args__ = (UniqueConstraint('user_id', 'friend_id', name='_user_friend_uc'),)

class PostViewModel(Base):
    __tablename__ = "POST_VIEWS_TABLE"
    
    id = Column("ID", Integer, Identity(start=1), primary_key=True)
    user_id = Column("USER_ID", Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column("POST_ID", Integer, ForeignKey("POSTS_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())

    # 🚀 THE UNIQUE FILTER CONSTRAINT SHIELD
    # Ensures a single User ID can generate exactly one view record row entry per Post ID
    __table_args__ = (
        UniqueConstraint('USER_ID', 'POST_ID', name='_user_post_view_uc'),
    )

    # Virtual Relationships mapping back handshakes
    post = relationship("PostModel", back_populates="views_log")

class PostShareModel(Base):
    __tablename__ = "POST_SHARES_TABLE"
    
    id = Column("ID", Integer, Identity(start=1), primary_key=True)
    user_id = Column("USER_ID", Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column("POST_ID", Integer, ForeignKey("POSTS_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    platform_target = Column("PLATFORM_TARGET", String(100), nullable=True, default="internal") 
    created_at = Column("CREATED_AT", DateTime, server_default=func.now())

    # 🚀 FIXED BINDING: The database column names are matched explicitly in uppercase
    __table_args__ = (
        UniqueConstraint('USER_ID', 'POST_ID', name='_user_post_share_uc'),
    )

    # Virtual Relationships
    post = relationship("PostModel", back_populates="shares_log")
    shared_by_user = relationship("UserModel", back_populates="shared_posts")
    
class PostModel(Base):
    __tablename__ = "POSTS_TABLE"

    id = Column("ID", Integer, Identity(start=1), primary_key=True)
    text_content = Column("TEXT_CONTENT", Text, nullable=True)
    media_url = Column("MEDIA_URL", String(512), nullable=True)
    media_type = Column("MEDIA_TYPE", String(50), nullable=True)
    
    # 🚀 ENFORCE LOWERCASE ATTRIBUTE NAME FOR SQLALCHEMY KEYWORD MATCHING
    thumbnail_url = Column("THUMBNAIL_URL", String(512), nullable=True)
    dislikes_count = Column("DISLIKES_COUNT", Integer, server_default="0", default=0, nullable=False)
    shares_count = Column("SHARES_COUNT", Integer, server_default="0", default=0, nullable=False)
    views_count = Column("VIEWS_COUNT", Integer, server_default="0", default=0, nullable=False)
    created_at = Column("CREATED_AT", DateTime, server_default=func.now(), index=True)
    user_id = Column("USER_ID", Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column("AUTHOR_ID", Integer, ForeignKey("USER_TABLE.ID"))
    likes_count = Column("LIKES_COUNT", Integer, server_default="0", default=0, nullable=False)
    # Explicitly bind this relationship to the author_id column
    author = relationship("UserModel", back_populates="posts", foreign_keys=[author_id])
    likes_log = relationship("PostLikeModel", back_populates="post", cascade="all, delete-orphan")
    shares_log = relationship("PostShareModel", back_populates="post", cascade="all, delete-orphan")
    views_log = relationship("PostViewModel", back_populates="post", cascade="all, delete-orphan")
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # 🌟 NEW SOCIAL INTERACTION COLUMNS TO ADD HERE:
    feeling = Column("FEELING", String(100), nullable=True)         # e.g., "Happy"
    activity = Column("ACTIVITY", String(100), nullable=True)       # e.g., "Eating dinner"
    checkin_place = Column("CHECKIN_PLACE", String(255), nullable=True) # e.g., "Starbucks Coffee"
    checkin_metadata = Column("CHECKIN_METADATA", Text, nullable=True)  # Stores coordinates as JSON string

    # Relationships (Your existing ones stay completely untouched)
    author = relationship("UserModel", back_populates="posts", foreign_keys=[author_id])
    likes_log = relationship("PostLikeModel", back_populates="post", cascade="all, delete-orphan")
    shares_log = relationship("PostShareModel", back_populates="post", cascade="all, delete-orphan")
    views_log = relationship("PostViewModel", back_populates="post", cascade="all, delete-orphan")
    
    # 🌟 NEW RELATIONSHIP FOR TAGGED FRIENDS LINK:
    tagged_friends = relationship("PostTagModel", back_populates="post", cascade="all, delete-orphan")

    viewed_by_users = relationship(
        "UserModel", 
        secondary="POST_VIEWS_TABLE", # Maps directly through your tracking table
        primaryjoin="PostModel.id == PostViewModel.post_id",
        secondaryjoin="UserModel.id == PostViewModel.user_id",
        viewonly=True # 👈 Crucial: Keeps this relationship read-only for high performance
    )

class PostTagModel(Base):
    __tablename__ = "POST_TAGS_TABLE"

    id = Column("ID", Integer, Identity(start=1), primary_key=True)
    post_id = Column("POST_ID", Integer, ForeignKey("POSTS_TABLE.ID", ondelete="CASCADE"), nullable=False)
    user_id = Column("USER_ID", Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False)

    # Relationships to link everything back up smoothly
    post = relationship("PostModel", back_populates="tagged_friends")
    
class BlockList(Base):
    __tablename__ = "BLOCK_LIST"

    id = Column(Integer, primary_key=True, index=True)
    # The user who triggers the block action
    blocker_id = Column(Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    # The user who is being blocked
    blocked_id = Column(Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Prevent duplicate blocks between the exact same two users
    __table_args__ = (UniqueConstraint('blocker_id', 'blocked_id', name='_blocker_blocked_uc'),)


class PostLikeModel(Base):
    __tablename__ = "POST_LIKES"

    id = Column(Integer, Identity(start=1), primary_key=True)
    user_id = Column(Integer, ForeignKey("USER_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    # 🛠️ FIX CASING: Changed "POSTS_TABLE.id" to match the table and column definitions exactly
    post_id = Column(Integer, ForeignKey("POSTS_TABLE.ID", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
   # 🚀 ADD THIS COLUMN: Maps directly to the new database column you created via SQL
    deleted_at = Column(DateTime, nullable=True, index=True)
    # ⚠️ CRUCIAL: A user can only like a specific post exactly once
    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='_user_post_like_uc'),)
    post = relationship("PostModel", back_populates="likes_log")

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Identity, UniqueConstraint
from src.utils.db import Base

class MediaGalleryModel(Base):
    __tablename__ = "USER_MEDIA_GALLERY"
    
    id = Column(Integer, Identity(start=1), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # 💾 Holds the explicit Cloudinary paths: "image" or "video"
    media_type = Column(String(20), nullable=False) 
    secure_url = Column(String(500), nullable=False)
    public_id = Column(String(250), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    
