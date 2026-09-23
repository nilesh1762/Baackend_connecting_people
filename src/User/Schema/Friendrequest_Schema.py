from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, date, timedelta, timezone


from src.User.model import RequestStatus

# Define India Standard Time Offset (+5:30)
IST_ZONE = timezone(timedelta(hours=5, minutes=30))
class FriendRequestCreate(BaseModel):
    receiver_id: int = Field(..., description="ID of the user receiving the request")

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: RequestStatus
    created_at: datetime

    @field_serializer('created_at')
    def serialize_to_ist(self, dt: datetime):
        # 1. Oracle stores it as naive UTC, so we mark it as UTC in Python first
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        # 2. Convert the UTC time directly into Indian Standard Time
        ist_datetime = dt.astimezone(IST_ZONE)
        
        # 3. Return it as an ISO string with the +05:30 tracking marker
        return ist_datetime.isoformat()

   
    class Config:
        from_attributes = True
