# create your middlewares classes here, any class defined here will be added to the app middlewares by default
from starlette import status
from starlette.responses import JSONResponse

from core.app import app


# Dependency for rate limiting (placeholder)
async def rate_limit_dependency():
    """Placeholder for rate limiting logic"""
    # Implement actual rate limiting (e.g., using Redis)
    pass


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": str(exc)}
    )
