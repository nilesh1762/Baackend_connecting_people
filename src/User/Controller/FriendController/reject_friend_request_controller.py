from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.User.model import FriendRequest, RequestStatus

def reject_friend_request_controller(request_id: int, current_user_id: int, db: Session):
    """
    Production-ready controller that safely handles your UniqueConstraint in BOTH directions.
    """
    # 🔍 Look for an interaction in either direction (You -> Them OR Them -> You)
    existing_record = db.query(FriendRequest).filter(
        or_(
            (FriendRequest.sender_id == current_user_id) & (FriendRequest.receiver_id == request_id),
            (FriendRequest.sender_id == request_id) & (FriendRequest.receiver_id == current_user_id)
        )
    ).first()

    if existing_record:
        # Scenario A: There is a pending request. Reject it!
        if existing_record.status == RequestStatus.PENDING:
            existing_record.status = RequestStatus.REJECTED
            db.commit()
            return {"message": "Friend request rejected successfully."}
        
        # Scenario B: It's already accepted or rejected, leave it alone.
        return {"message": "Interaction already recorded."}

    # ➕ Scenario C: Pure suggestion dismiss. No row exists in either direction.
    # It is safe to insert a new row without violating the unique constraint.
    new_rejection = FriendRequest(
        sender_id=current_user_id,
        receiver_id=request_id,
        status=RequestStatus.REJECTED
    )
    
    try:
        db.add(new_rejection)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update suggestion mapping due to database integrity."
        )
    
    return {"message": "Friend suggestion dismissed successfully."}
