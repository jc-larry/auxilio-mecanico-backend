import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequireRoles, get_current_user
from app.core.permissions import RoleEnum
from app.models.usuario import Usuario
from app.schemas.auth import UserCreate, UserResponse
from app.schemas.user import PaginatedUserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedUserResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = UserService(db)
    items, total = await service.list_all(page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1

    return PaginatedUserResponse(
        items=[UserResponse.from_model(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = UserService(db)
    user = await service.get_by_id_with_permissions(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserResponse.from_model(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = UserService(db)
    existing_email = await service.get_by_email(payload.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")
        
    existing_username = await service.get_by_username(payload.username)
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario ya está en uso")

    user = await service.create(payload)
    # The default create doesn't assign roles but we can call update right away to add them if provided
    # Wait, UserCreate doesn't have roles. If we wanted to create with roles we would need a new schema
    # The requirement is just simple CRUD, we can update roles in a separate request or just return the user
    return UserResponse.from_model(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = UserService(db)
    user = await service.update(user_id, payload, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserResponse.from_model(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminarte a ti mismo")
        
    service = UserService(db)
    user = await service.update(user_id, UserUpdate(is_active=False), current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
