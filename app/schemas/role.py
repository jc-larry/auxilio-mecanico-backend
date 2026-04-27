from pydantic import BaseModel, Field

class PermissionResponse(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_attributes(cls, obj) -> "PermissionResponse":
        return cls.model_validate(obj)

class RoleResponse(BaseModel):
    id: int
    nombre: str
    permisos: list[PermissionResponse]

    model_config = {"from_attributes": True}

    @classmethod
    def from_attributes(cls, obj) -> "RoleResponse":
        return cls.model_validate(obj)

class RoleCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    permisos_ids: list[int] = []

class RoleUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=50)
    permisos_ids: list[int] | None = None


