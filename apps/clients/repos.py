from apps.clients.models import Client
from bases.base_orm import BaseORM


class ClientRepository(BaseORM):
    model = Client

