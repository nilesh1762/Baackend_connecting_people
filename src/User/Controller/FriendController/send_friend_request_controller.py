from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import FriendRequest, RequestStatus, Friendship, UserModel

def send_friend_request_controller(receiver_id: int, current_user_id: int, db: Session):
    """Business logic controller to handle initiating a friend request."""
    # Prevent self-requests
    if current_user_id == receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot send a friend request to yourself."
        )

    # Check if the receiver exists in the database
    receiver_exists = db.query(UserModel).filter(UserModel.id == receiver_id).first()
    if not receiver_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with ID {receiver_id} does not exist."
        )
        
    # Rule 1: Check if already friends
    already_friends = db.query(Friendship).filter(
        (Friendship.user_id == current_user_id) & (Friendship.friend_id == receiver_id)
    ).first()
    if already_friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You are already friends with this user."
        )

    # Rule 2: Check for existing pending request from sender
    existing_req = db.query(FriendRequest).filter(
        (FriendRequest.sender_id == current_user_id) & 
        (FriendRequest.receiver_id == receiver_id) & 
        (FriendRequest.status == RequestStatus.PENDING)
    ).first()
    if existing_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A friend request is already pending."
        )

    # Rule 3: Check if the opposite request is already waiting
    opposite_req = db.query(FriendRequest).filter(
        (FriendRequest.sender_id == receiver_id) & 
        (FriendRequest.receiver_id == current_user_id) & 
        (FriendRequest.status == RequestStatus.PENDING)
    ).first()
    if opposite_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This user has already sent you a request. Accept it instead."
        )

    # Write request to database
    new_request = FriendRequest(sender_id=current_user_id, receiver_id=receiver_id)
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request
