from pydantic import BaseModel, ConfigDict, Field
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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., alias="id")
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    moderation_status: str = "approved"
    thumbnail_url: Optional[str] = None
    created_at: datetime
    user_id: int
    feed_item_id: Optional[str] = None
    feed_created_at: Optional[datetime] = None
    is_repost: bool = False
    visibility: str = "anyone"
    reposted_at: Optional[datetime] = None
    reposted_by: Optional[AuthorSummarySchema] = None
    has_liked: bool = False
    
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
    tagged_friends: List[TaggedUserResponse] = Field(default_factory=list)

class PostDetailResponse(PostResponse):
    comments_count: int = Field(default=0)
    has_liked: bool = False
