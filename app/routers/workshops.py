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
)
from app.schemas.common import PaginatedResponse
from app.services.workshop_service import WorkshopService
from app.models.usuario import Usuario
from app.models.propietario import Propietario

router = APIRouter(prefix="/workshops", tags=["Workshops"])

@router.get("", response_model=PaginatedResponse[WorkshopResponse])
async def list_workshops(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.TALLERES_VER])),
):
    service = WorkshopService(db)
    
    # Filter by propietario_id if not admin
    propietario_id = None
    user_roles = [r.nombre for r in current_user.roles]
    is_admin = "Administrador" in user_roles
    is_owner = "Propietario" in user_roles

    if not is_admin and is_owner:
        if not current_user.propietario:
            # Ensure Propietario record exists
            new_propietario = Propietario(usuario_id=current_user.id)
            db.add(new_propietario)
            await db.commit()
            await db.refresh(current_user)
        
        if current_user.propietario:
            propietario_id = current_user.propietario.id
        else:
            # Fallback if creation failed or something is wrong
            # Return empty list or raise error
            return PaginatedResponse(items=[], total=0, page=page, per_page=per_page, pages=0)
        
    items, total = await service.list_all(page, per_page, propietario_id)
    pages = math.ceil(total / per_page) if total > 0 else 1
    
    return PaginatedResponse(
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
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.TALLERES_CREAR])),
):
    service = WorkshopService(db)
    propietario_id = None
    
    # Check if user is owner and ensure record exists
    user_roles = [r.nombre for r in current_user.roles]
    is_admin = "Administrador" in user_roles
    is_owner = "Propietario" in user_roles
    
    if not is_admin and is_owner:
        if not current_user.propietario:
            # Create Propietario record on the fly if missing
            new_propietario = Propietario(usuario_id=current_user.id)
            db.add(new_propietario)
            await db.commit()
            await db.refresh(current_user)
        
        if current_user.propietario:
            propietario_id = current_user.propietario.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo establecer el vínculo de propiedad para este usuario."
            )
        
    return await service.create(payload, propietario_id)

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
