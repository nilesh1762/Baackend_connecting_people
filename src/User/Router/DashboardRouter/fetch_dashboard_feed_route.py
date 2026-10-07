from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Local application layer component tracking
from src.utils.db import init_db
from src.utils.security import get_current_user_id
from src.User.Schema.dashboard_schema import DashboardFeedResponseSchema
from src.User.Controller.DashboardController.dashboard_controllers import get_first_time_dashboard_feed_controller

user_router = APIRouter(prefix="/user", tags=["Content Delivery"])

@user_router.get(
    "/dashboard-feed", 
    response_model=DashboardFeedResponseSchema, 
    status_code=status.HTTP_200_OK
)
def fetch_dashboard_feed(
    limit: int = 10,
    offset: int = 0,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(init_db)
):
    """
    📱 WORLD CLASS FIRST-TIME LOGIN USER FEED ENDPOINT
    Aggregates multi-channel content types (Text, Quotes, Videos, Images) sorted 
    by location and user psychographic traits compiled from all 4 onboarding questions.
    """
    try:
        feed_data = get_first_time_dashboard_feed_controller(
            current_user_id=current_user_id, 
            db=db, 
            offset=offset,
            limit=limit
        )
        return feed_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while compiling your personalized dashboard feed: {str(e)}"
        )
