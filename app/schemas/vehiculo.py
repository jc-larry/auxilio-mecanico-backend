from pydantic import BaseModel

class VehiculoResponse(BaseModel):
    id: int
    cliente_id: int
    marca: str
    modelo: str
    placa: str
    anio: int
    color: str

    model_config = {"from_attributes": True}
