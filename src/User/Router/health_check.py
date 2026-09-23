from fastapi import FastAPI, Depends, HTTPException, APIRouter,status


router = APIRouter(prefix="/user")
# 🌐 Light public endpoint for React connection checks
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Lightweight health check endpoint.
    Bypasses authentication so the React UI can test server availability.
    """
    return {
        "status": "online",
        "message": "Backend server is running successfully"
    }

