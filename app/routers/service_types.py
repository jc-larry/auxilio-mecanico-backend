from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import RequirePermissions
from app.core.permissions import PermissionEnum
from app.models.usuario import Usuario
from app.schemas.service_type import (
    TipoServicioCreate,
    TipoServicioResponse,
    TipoServicioUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.service_type_service import ServiceTypeService

router = APIRouter(prefix="/service-types", tags=["Service Types"])

@router.get("", response_model=PaginatedResponse[TipoServicioResponse])
async def list_service_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SERVICIOS_VER])),
):
    service = ServiceTypeService(db)
    items, total, pages = await service.list_all(page, per_page)
    
    return PaginatedResponse(
        items=[TipoServicioResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

@router.get("/{service_type_id}", response_model=TipoServicioResponse)
async def get_service_type(
    service_type_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SERVICIOS_VER])),
):
    service = ServiceTypeService(db)
    st = await service.get_by_id(service_type_id)
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de servicio no encontrado")
    return TipoServicioResponse.model_validate(st)

@router.post("", response_model=TipoServicioResponse, status_code=status.HTTP_201_CREATED)
async def create_service_type(
    payload: TipoServicioCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SERVICIOS_CREAR])),
):
    service = ServiceTypeService(db)
    
    if await service.get_by_nombre(payload.nombre):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un tipo de servicio con ese nombre"
        )
        
    st = await service.create(payload)
    return TipoServicioResponse.model_validate(st)

@router.patch("/{service_type_id}", response_model=TipoServicioResponse)
async def update_service_type(
    service_type_id: int,
    payload: TipoServicioUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SERVICIOS_EDITAR])),
):
    service = ServiceTypeService(db)
    
    if payload.nombre:
        existing = await service.get_by_nombre(payload.nombre)
        if existing and existing.id != service_type_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro tipo de servicio con ese nombre"
            )
            
    st = await service.update(service_type_id, payload)
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de servicio no encontrado")
        
    return TipoServicioResponse.model_validate(st)

@router.delete("/{service_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_type(
    service_type_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.SERVICIOS_ELIMINAR])),
):
    service = ServiceTypeService(db)
    try:
        deleted = await service.delete(service_type_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de servicio no encontrado")
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el tipo de servicio porque está en uso por una solicitud"
        )
