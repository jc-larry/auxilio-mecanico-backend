from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
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
    username: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None = None
    roles: list[str] = []
    permissions: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj) -> "UserResponse":
        return cls(
            id=obj.id,
            email=obj.email,
            username=obj.username,
            full_name=obj.nombre,
            is_active=obj.estado,
            is_verified=obj.is_verified,
            created_at=obj.fecha_registro,
            last_login=obj.last_login,
            roles=[r.nombre for r in getattr(obj, "roles", [])],
            permissions=list({p.nombre for r in getattr(obj, "roles", []) for p in getattr(r, "permisos", [])})
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
