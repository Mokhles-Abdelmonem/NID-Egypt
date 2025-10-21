from fastapi import Header, HTTPException, status, Depends

from apps.clients.models import Client
from apps.clients.services import ClientService


async def verify_service_key(x_api_key: str = Header(...), service: ClientService = Depends(ClientService)):
    client: Client = await service.repo.first(api_key=x_api_key)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return client
