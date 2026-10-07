from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.User.model import BlockList, FriendRequest

def block_user_controller(
    target_id: int,
    db: Session,
    current_user_id: int
) -> dict:
    """Handles the business logic for blocking a user, checking guards, and cleansing connections."""
    
    # 1. Guardrail: Can't block yourself
    if current_user_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot block yourself."
        )

    # 2. Check if already blocked
    existing_block = db.query(BlockList).filter(
        and_(BlockList.blocker_id == current_user_id, BlockList.blocked_id == target_id)
    ).first()

    if existing_block:
        return {"message": "User is already blocked."}

    # 3. Create the block record
    new_block = BlockList(blocker_id=current_user_id, blocked_id=target_id)
    db.add(new_block)
    
    # 4. Automatically sever pending requests or interactions between both users
    db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == current_user_id) & (FriendRequest.receiver_id == target_id)) |
        ((FriendRequest.sender_id == target_id) & (FriendRequest.receiver_id == current_user_id))
    ).delete(synchronize_session=False)

    db.commit()
    return {"message": f"User {target_id} has been blocked successfully."}
