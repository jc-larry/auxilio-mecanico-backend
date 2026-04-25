from pydantic import BaseModel, Field
from typing import Generic, TypeVar

class WorkshopBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    direccion: str = Field(..., min_length=5, max_length=255)
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    telefono: str = Field(..., min_length=7, max_length=20)
    estado: bool = True

class WorkshopCreate(WorkshopBase):
    pass

class WorkshopUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=100)
    direccion: str | None = Field(None, min_length=5, max_length=255)
    latitud: float | None = Field(None, ge=-90, le=90)
    longitud: float | None = Field(None, ge=-180, le=180)
    telefono: str | None = Field(None, min_length=7, max_length=20)
    estado: bool | None = None

class WorkshopResponse(WorkshopBase):
    id: int

    model_config = {"from_attributes": True}

T = TypeVar("T")

class PaginatedWorkshopResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
