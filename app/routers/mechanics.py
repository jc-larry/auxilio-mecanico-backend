import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.mechanic import (
    MechanicCreate,
    MechanicResponse,
    MechanicStats,
    MechanicUpdate,
    PaginatedResponse,
)
from app.services.mechanic_service import MechanicService

router = APIRouter(prefix="/mechanics", tags=["Mechanics"])


@router.get("", response_model=PaginatedResponse[MechanicResponse])
async def list_mechanics(
    available: bool | None = Query(None),
    specialty: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = MechanicService(db)
    items, total = await service.list_all(available, specialty, page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1

    return PaginatedResponse(
        items=[MechanicResponse.from_model(m) for m in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/stats", response_model=MechanicStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = MechanicService(db)
    return await service.get_stats()


@router.get("/{mechanic_id}", response_model=MechanicResponse)
async def get_mechanic(
    mechanic_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = MechanicService(db)
    m = await service.get_by_id(mechanic_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mecánico no encontrado")
    return MechanicResponse.from_model(m)


@router.post("", response_model=MechanicResponse, status_code=status.HTTP_201_CREATED)
async def create_mechanic(
    payload: MechanicCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MechanicService(db)
    m = await service.create(payload, current_user.id)
    return MechanicResponse.from_model(m)


@router.patch("/{mechanic_id}", response_model=MechanicResponse)
async def update_mechanic(
    mechanic_id: int,
    payload: MechanicUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = MechanicService(db)
    m = await service.update(mechanic_id, payload)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mecánico no encontrado")
    return MechanicResponse.from_model(m)


@router.delete("/{mechanic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mechanic(
    mechanic_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = MechanicService(db)
    deleted = await service.delete(mechanic_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mecánico no encontrado")
