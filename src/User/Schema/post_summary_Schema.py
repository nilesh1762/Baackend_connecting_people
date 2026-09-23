from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List
from src.User.Schema.Userregistraion_Schema import UserResponse

class AuthorSummarySchema(BaseModel):
    id: int
    firstname: str
    lastname: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True # Enables strict SQLAlchemy conversion loops natively

class TaggedUserResponse(BaseModel):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: int = Field(..., alias="id")
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    user_id: int
    
    # 🚀 THE CRITICAL ADDITIONS: Map your database performance performance counters here
    likes_count: int = Field(default=0)
    dislikes_count: int = Field(default=0)
    shares_count: int = Field(default=0)
    views_count: int = Field(default=0) # Tracks silent background view increments
    
    # Nested object mapping author tables data columns cleanly
    author: Optional[AuthorSummarySchema] = None

     #  ADD THESE FIELDS TO MATCH YOUR NEW ORACLE COLUMNS AND RELATIONSHIPS:
    feeling: Optional[str] = None
    activity: Optional[str] = None
    checkin_place: Optional[str] = None
    checkin_metadata: Optional[str] = None # Raw JSON string tracking data output
    tagged_friends: List[TaggedUserResponse] = [] #  Automatically loads table joins!

class Config:
        from_attributes = True # 🚀 CRUCIAL: Tells Pydantic v2 to parse SQLAlchemy attributes automatically
        populate_by_name = True
