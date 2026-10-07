from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.User.model import Friendship, FriendRequest, RequestStatus

def unfriend_user_controller(
    friend_id: int,
    db: Session,
    current_user_id: int
) -> dict:
    """Handles soft-deleting friendship links and resetting related friend requests."""
    
    # 1. Search for active friendships across both bi-directional rows
    friendship_rows = db.query(Friendship).filter(
        (Friendship.is_deleted == False) & (
            ((Friendship.user_id == current_user_id) & (Friendship.friend_id == friend_id)) |
            ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user_id))
        )
    ).all()

    if not friendship_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Friend relationship not found."
        )

    # 2. Soft-delete the bi-directional friendship records
    for row in friendship_rows:
        row.is_deleted = True

    # 3. Reset request tables back to REJECTED so future additions are allowed
    db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == current_user_id) & (FriendRequest.receiver_id == friend_id)) |
        ((FriendRequest.sender_id == friend_id) & (FriendRequest.receiver_id == current_user_id))
    ).update({"status": RequestStatus.REJECTED}, synchronize_session=False)

    db.commit()
    return {"message": "User unfriended successfully."}
