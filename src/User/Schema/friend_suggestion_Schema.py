from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional

class MutualFriendMinimalResponse(BaseModel):
    id: int
    firstname: str
    lastname: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True

class UserSuggestionResponse(BaseModel):
    id: int
    email: EmailStr
    firstname: str | None = Field(default=None, alias="firstName")
    lastname: str | None = Field(default=None, alias="lastName")
    
    # 🟢 CHANGE: validation_alias changed to lowercase "profile_image_url"
    profile_image_url: Optional[str] = Field(
        default=None, 
        validation_alias="profile_image_url", 
        serialization_alias="profile_image_url"
    )
    
    # 🟢 CHANGE: Also update created_at to use a validation alias if your controller outputs 'created_at'
    created_at: datetime = Field(
        validation_alias="created_at", 
        serialization_alias="createdAt"
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class FriendSuggestionWrapper(BaseModel):
    """Schema representing the wrapper matching the controller's dict output."""
    user: UserSuggestionResponse
    mutual_friends: List[MutualFriendMinimalResponse] = Field(default=[], serialization_alias="mutualFriends")

    class Config:
        from_attributes = True