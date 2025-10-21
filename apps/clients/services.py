from pydantic import BaseModel

from apps.clients.repos import ClientRepository
from apps.clients.schemas import ServiceClientResponse
from bases.business_logic import CreateOperation, ListOperation, RetrieveOperation


class ClientService(CreateOperation, ListOperation, RetrieveOperation):
    repo = ClientRepository
    schema_out = ServiceClientResponse

    async def pre_create(self, data: BaseModel):
        """
        Pre-processing hook that is executed before creating a resource.
        """
        data = data.model_dump(exclude_none=True)
        data["api_key"] = self.repo.model.generate_api_key()
        return data