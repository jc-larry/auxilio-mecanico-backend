from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100)
    is_active: bool | None = None
    roles: list[str] | None = None


class PaginatedUserResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class UserPasswordUpdate(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=50)
