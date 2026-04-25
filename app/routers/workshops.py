import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import RequirePermissions
from app.core.permissions import PermissionEnum
from app.schemas.workshop import (
    WorkshopCreate,
    WorkshopResponse,
    WorkshopUpdate,
    PaginatedWorkshopResponse,
)
from app.services.workshop_service import WorkshopService
from app.models.usuario import Usuario

router = APIRouter(prefix="/workshops", tags=["Workshops"])

@router.get("", response_model=PaginatedWorkshopResponse[WorkshopResponse])
async def list_workshops(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.TALLERES_VER])),
):
    service = WorkshopService(db)
    items, total = await service.list_all(page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1
    
    return PaginatedWorkshopResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )

@router.post("", response_model=WorkshopResponse, status_code=status.HTTP_201_CREATED)
async def create_workshop(
    payload: WorkshopCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.TALLERES_CREAR])),
):
    service = WorkshopService(db)
    return await service.create(payload)

@router.patch("/{workshop_id}", response_model=WorkshopResponse)
async def update_workshop(
    workshop_id: int,
    payload: WorkshopUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.TALLERES_EDITAR])),
):
    service = WorkshopService(db)
    workshop = await service.update(workshop_id, payload)
    if not workshop:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return workshop

@router.delete("/{workshop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workshop(
    workshop_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.TALLERES_ELIMINAR])),
):
    service = WorkshopService(db)
    if not await service.delete(workshop_id):
        raise HTTPException(status_code=404, detail="Taller no encontrado")
