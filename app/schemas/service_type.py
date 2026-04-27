from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class TipoServicioBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    precio_base: Decimal = Field(..., ge=0)

class TipoServicioCreate(TipoServicioBase):
    pass

class TipoServicioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    precio_base: Optional[Decimal] = Field(None, ge=0)

class TipoServicioResponse(TipoServicioBase):
    id: int

    model_config = {"from_attributes": True}


