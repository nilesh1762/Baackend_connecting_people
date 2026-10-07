from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import FriendRequest, RequestStatus, Friendship

def accept_friend_request_controller(request_id: int, current_user_id: int, db: Session):
    """Business logic controller to accept a friend request and create bi-directional links."""
    # Find the pending request meant for the logged-in user
    req = db.query(FriendRequest).filter(
        (FriendRequest.id == request_id) & 
        (FriendRequest.receiver_id == current_user_id) & 
        (FriendRequest.status == RequestStatus.PENDING)
    ).first()
    
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Pending friend request not found."
        )

    # Update request state tracking table
    req.status = RequestStatus.ACCEPTED

    # Create bi-directional relationships
    friendship_1 = Friendship(user_id=req.sender_id, friend_id=req.receiver_id)
    friendship_2 = Friendship(user_id=req.receiver_id, friend_id=req.sender_id)
    
    db.add_all([friendship_1, friendship_2])
    db.commit()
    
    return {"message": "Friend request accepted successfully."}
