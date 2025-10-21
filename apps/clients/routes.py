from fastapi import APIRouter, Depends

from apps.clients.schemas import ServiceClientResponse, ServiceClientCreate
from apps.clients.services import ClientService


router = APIRouter(prefix="/clients", tags=["Service Clients"])


@router.post("/", response_model=ServiceClientResponse)
async def create_client(data: ServiceClientCreate, service: ClientService = Depends(ClientService)):
    client = await service.create(data=data)
    return client


@router.get("/", response_model=list[ServiceClientResponse])
async def list_clients(
        limit: int = 100,
        offset: int = 0,
        service: ClientService = Depends(ClientService)
):
    return await service.list(limit=limit, offset=offset)
