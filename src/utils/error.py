import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, DBAPIError

logger = logging.getLogger("app_errors")

# 🛠️ ADD THIS HELPER UTILITY AT THE TOP
def get_cors_headers(request: Request) -> dict:
    """Dynamically captures and builds cross-origin approval blocks for strict browsers like Edge."""
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    return headers

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unhandled system exceptions to prevent unformatted 500 server crashes."""
    logger.error(f"UNHANDLED EXCEPTION on path {request.url.path}: {str(exc)}", exc_info=True)
    
    # Also attach the real exception text inside development payloads temporarily 
    # to see exactly why it's breaking in Edge!
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "debug_message": str(exc) # 💡 Temporary trace line to catch the real bug
        },
        headers=get_cors_headers(request) # 🟢 THE EDGE CORS FIX
    )

async def sqlalchemy_integrity_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Intercepts database constraints violations (duplicate entries, foreign key issues)."""
    logger.warning(f"DATABASE INTEGRITY FAULT on path {request.url.path}: {str(exc)}")
    
    error_msg = "Database constraint violation occurred."
    if "ORA-00001" in str(exc) or "UniqueConstraint" in str(exc):
        error_msg = "This record already exists in the system."
    elif "ORA-02291" in str(exc) or "ForeignKey" in str(exc):
        error_msg = "Referenced parent record could not be found."
        
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": error_msg},
        headers=get_cors_headers(request) # 🟢 THE EDGE CORS FIX
    )

async def sqlalchemy_db_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    """Intercepts driver level connection drops and query execution failures."""
    logger.critical(f"DATABASE CONNECTION OR TIMEOUT FAULT: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database service is temporarily unavailable. Please try again shortly."},
        headers=get_cors_headers(request) # 🟢 THE EDGE CORS FIX
    )
