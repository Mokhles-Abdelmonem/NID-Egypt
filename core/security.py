# Create your routes here.
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, UTC
from core.settings import settings


def verify_service_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.API_JWT_SECRET, algorithms=[settings.API_JWT_ALGORITHM])
        if payload.get("service") != "ai-agent":
            raise HTTPException(status_code=403, detail="Unauthorized service")
        exp = payload.get("exp", 0)
        if datetime.now(UTC).timestamp() > exp:
            raise HTTPException(status_code=403, detail="Unauthorized service")

    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    return payload
