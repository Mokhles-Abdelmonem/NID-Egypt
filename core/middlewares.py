from starlette import status
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime


from apps.clients.services import ClientService
from apps.egypt_national_id.services import ApiUsageService
from bases.model import Base
from bases.session_manager import session_manager
from core.app import app

import time
from fastapi import Request, HTTPException

from core.settings import settings

RATE_LIMIT_STORAGE = {}


@app.on_event("startup")
async def startup():
    await session_manager.create_all_tables(Base)
    print("Database tables created.")



async def rate_limit_dependency(request: Request):
    """Simple in-memory rate limiter per API key or IP."""
    # Identify client (by API key header or IP address)
    api_key = request.headers.get("x-api-key", request.client.host)
    now = time.time()

    # Get request history for this client
    timestamps = RATE_LIMIT_STORAGE.get(api_key, [])

    # Keep only recent requests (within the window)
    timestamps = [t for t in timestamps if now - t < settings.WINDOW_SECONDS]

    # Check if limit exceeded
    if len(timestamps) >= settings.MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    # Record this request
    timestamps.append(now)
    RATE_LIMIT_STORAGE[api_key] = timestamps


@app.middleware("http")
async def add_rate_limiter(request: Request, call_next):
    try:
        await rate_limit_dependency(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    response = await call_next(request)
    return response



# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": str(exc)}
    )


class APICallTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        async with session_manager.async_session() as session:
            client_service = ClientService(request, session)
            api_usage_service = ApiUsageService(request, session)

            start_time = time.time()
            client = None
            api_key = request.headers.get("x-api-key")
            if api_key:
                client = await client_service.repo.first(api_key=api_key)

            response = await call_next(request)
            duration = round(time.time() - start_time, 3)

            await api_usage_service.repo.create(
                client_id=client.id if client else None,
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration=duration,
                timestamp=datetime.now()
            )

        return response
app.add_middleware(APICallTrackingMiddleware)

