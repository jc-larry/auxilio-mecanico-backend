from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr

    full_name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    id: int
    email: str

    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None = None
    roles: list[str] = []
    permissions: list[str] = []
    taller_id: int | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj) -> "UserResponse":
        from sqlalchemy import inspect
        
        # Obtener roles y permisos solo si están cargados para evitar MissingGreenlet
        roles_list = []
        permissions_list = []
        
        insp = inspect(obj)
        if "roles" not in insp.unloaded:
            roles_list = [r.nombre for r in obj.roles]
            # También verificar si los permisos de los roles están cargados
            for r in obj.roles:
                r_insp = inspect(r)
                if "permisos" not in r_insp.unloaded:
                    permissions_list.extend([p.nombre for p in r.permisos])
        
        # Eliminar duplicados de permisos
        permissions_list = list(set(permissions_list))
        
        # Obtener taller_id
        taller_id = None
        if "mecanico" not in insp.unloaded and obj.mecanico:
            taller_id = obj.mecanico.taller_id
        elif "propietario" not in insp.unloaded and obj.propietario:
            prop_insp = inspect(obj.propietario)
            if "talleres" not in prop_insp.unloaded and obj.propietario.talleres:
                taller_id = obj.propietario.talleres[0].id
        
        return cls(
            id=obj.id,
            email=obj.email,

            full_name=obj.nombre,
            is_active=obj.estado,
            is_verified=getattr(obj, "is_verified", False),
            created_at=getattr(obj, "fecha_registro", datetime.now()),
            last_login=getattr(obj, "last_login", None),
            roles=roles_list,
            permissions=permissions_list,
            taller_id=taller_id
        )



class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
