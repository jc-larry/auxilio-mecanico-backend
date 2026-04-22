import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, RequirePermissions
from app.core.permissions import PermissionEnum
from app.models.usuario import Usuario
from app.schemas.service_request import (
    PaginatedResponse,
    ServiceRequestCreate,
    ServiceRequestResponse,
    ServiceRequestStats,
    ServiceRequestUpdate,
)
from app.services.service_request_service import ServiceRequestService

router = APIRouter(prefix="/service-requests", tags=["Service Requests"])


@router.get("", response_model=PaginatedResponse[ServiceRequestResponse])
async def list_service_requests(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SOLICITUDES_VER])),
):
    service = ServiceRequestService(db)
    items, total = await service.list_all(status_filter, page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1

    return PaginatedResponse(
        items=[ServiceRequestResponse.from_model(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/stats", response_model=ServiceRequestStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SOLICITUDES_VER])),
):
    service = ServiceRequestService(db)
    return await service.get_stats()


@router.get("/{request_id}", response_model=ServiceRequestResponse)
async def get_service_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SOLICITUDES_VER])),
):
    service = ServiceRequestService(db)
    sr = await service.get_by_id(request_id)
    if not sr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return ServiceRequestResponse.from_model(sr)


@router.post("", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_service_request(
    payload: ServiceRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.SOLICITUDES_CREAR])),
):
    service = ServiceRequestService(db)
    sr = await service.create(payload, current_user.id)
    return ServiceRequestResponse.from_model(sr)


@router.patch("/{request_id}", response_model=ServiceRequestResponse)
async def update_service_request(
    request_id: int,
    payload: ServiceRequestUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SOLICITUDES_REPROGRAMAR])),
):
    service = ServiceRequestService(db)
    sr = await service.update(request_id, payload)
    if not sr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return ServiceRequestResponse.from_model(sr)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SOLICITUDES_RECHAZAR])),
):
    service = ServiceRequestService(db)
    deleted = await service.delete(request_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
