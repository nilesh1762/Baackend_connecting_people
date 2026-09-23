from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.utils.db import init_db
from src.User.Controller.friend_suggestions_controller import get_advanced_friend_suggestions_controller
from src.utils.security import get_current_user_id
# Import the new schema wrapper
from src.User.Schema.friend_suggestion_Schema import FriendSuggestionWrapper

user_router = APIRouter(prefix="/user", tags=["Friendships"])
# Update the response_model here
@user_router.get("/friends/suggestions", response_model=List[FriendSuggestionWrapper])

def get_friend_suggestions(
    limit: int = Query(default=10, ge=1, le=50, description="Number of suggestions to return"),
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get friend suggestions (friends of friends) ranked by mutual connections.
    """
    # try:
        # The controller output matches the wrapper dictionary structure perfectly
    return get_advanced_friend_suggestions_controller(
            current_user_id=current_user_id,
            db=db,
            limit=limit
        )
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="An error occurred while fetching friend suggestions."
    #     )
