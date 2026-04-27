import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RequireRoles
from app.core.permissions import RoleEnum
from app.models.usuario import Usuario
from app.schemas.role import (
    RoleCreate, 
    RoleUpdate, 
    RoleResponse, 
    PermissionResponse
)
from app.schemas.common import PaginatedResponse
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])
permissions_router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get("", response_model=PaginatedResponse[RoleResponse])
async def list_roles(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = RoleService(db)
    items, total = await service.list_all(page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    
    return PaginatedResponse(
        items=[RoleResponse.from_attributes(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )

@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = RoleService(db)
    role = await service.create(payload)
    return RoleResponse.from_attributes(role)

@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = RoleService(db)
    role = await service.update(role_id, payload)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return RoleResponse.from_attributes(role)

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = RoleService(db)
    success = await service.delete(role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")

# ── Permissions ──────────────────────────────────────────────────────

@permissions_router.get("", response_model=list[PermissionResponse])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR])),
):
    service = RoleService(db)
    permissions = await service.get_all_permissions()
    return [PermissionResponse.from_attributes(p) for p in permissions]
