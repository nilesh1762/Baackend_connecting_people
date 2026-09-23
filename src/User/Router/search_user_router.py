from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Controller.search_user_controller import search_users_by_username_controller


user_router = APIRouter(prefix="/user", tags=["Global Navigation Search"])

@user_router.get("/search/autocomplete", status_code=status.HTTP_200_OK)
async def search_users_autocomplete(
    q: str = Query("", description="The partial name typed into the header search bar"),
    db: Session = Depends(init_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Real-time autocomplete dropdown endpoint for navigation search bars.
    Returns matched user profiles while safely excluding all mutual blocked configurations.
    """
    print(f"\n[DEBUG ROUTER] Raw query 'q' received from client: '{q}'")
    return search_users_by_username_controller(
        db=db, 
        query_string=q, 
        current_user_id=current_user_id
    )
