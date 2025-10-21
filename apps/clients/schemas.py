from pydantic import BaseModel

class ServiceClientBase(BaseModel):
    name: str
    description: str | None = None

class ServiceClientCreate(ServiceClientBase):
    pass

class ServiceClientResponse(ServiceClientBase):
    id: int
    api_key: str

    class Config:
        from_attributes = True
