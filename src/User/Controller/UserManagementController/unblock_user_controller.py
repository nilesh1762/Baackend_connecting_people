from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.User.model import BlockList

def unblock_user_controller(
    target_id: int,
    db: Session,
    current_user_id: int
) -> dict:
    """Handles business logic for searching and removing a user block record."""
    
    # 1. Search for an active block matching this specific relationship configuration
    block_record = db.query(BlockList).filter(
        and_(BlockList.blocker_id == current_user_id, BlockList.blocked_id == target_id)
    ).first()

    # 2. Guardrail validation check
    if not block_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Block record not found."
        )

    # 3. Clean record entries from Oracle tables
    db.delete(block_record)
    db.commit()
    
    return {"message": f"User {target_id} has been unblocked successfully."}
