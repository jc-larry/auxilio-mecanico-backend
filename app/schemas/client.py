from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class ClientResponse(BaseModel):
    id: int
    usuario_id: int
    nombre: str
    email: str

    model_config = {"from_attributes": True}

class PaginatedClientResponse(BaseModel):
    items: list[ClientResponse]
    total: int
    page: int
    per_page: int
    pages: int
