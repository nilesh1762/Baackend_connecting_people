from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class MutualFriendDetail(BaseModel):
    id: int
    firstname: str
    lastname: Optional[str] = None
    profile_image_url: Optional[str] = None 
    localization: Optional[str] = "Unknown"

class FriendProfileResponse(BaseModel):
    friend_id: int
    firstname: str
    email: str
    profile_image_url: str
    friends_since: datetime
    mutual_friends_count: int
    isOnline: bool = Field(default=False, serialization_alias="isOnline", assignment_exclude=True)
    statusPresence: str = Field(default="offline", serialization_alias="statusPresence", validation_alias="status_presence")
    mutual_friends: List[MutualFriendDetail]
    class Config:
        from_attributes = True