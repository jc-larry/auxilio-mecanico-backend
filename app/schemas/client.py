from pydantic import BaseModel


class ClientResponse(BaseModel):
    id: int
    usuario_id: int
    nombre: str
    email: str

    model_config = {"from_attributes": True}


