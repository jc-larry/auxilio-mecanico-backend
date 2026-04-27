import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, RequirePermissions, get_user_taller_id
from app.core.permissions import PermissionEnum
from app.models.usuario import Usuario
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryStats,
    RestockRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=PaginatedResponse[InventoryItemResponse])
async def list_inventory(
    critical: bool = Query(False),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_VER])),
):
    taller_id = get_user_taller_id(current_user)
    service = InventoryService(db)
    items, total = await service.list_all(critical, category, page, per_page, taller_id)
    pages = math.ceil(total / per_page) if total > 0 else 1

    return PaginatedResponse(
        items=[InventoryItemResponse.from_model(rep, inv) for rep, inv in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/stats", response_model=InventoryStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_VER])),
):
    taller_id = get_user_taller_id(current_user)
    service = InventoryService(db)
    return await service.get_stats(taller_id)


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_VER])),
):
    taller_id = get_user_taller_id(current_user)
    service = InventoryService(db)
    result = await service.get_by_repuesto_id(item_id, taller_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    
    rep, inv = result
    return InventoryItemResponse.from_model(rep, inv)


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_AGREGAR])),
):
    taller_id = get_user_taller_id(current_user)
    if not taller_id:
        # Si es admin sin taller, usar taller por defecto para la creación o fallar
        # Por ahora permitimos usar el taller por defecto en el servicio si es admin
        pass

    service = InventoryService(db)
    existing = await service.get_by_sku(payload.sku)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU ya existe")
    
    item = await service.create(payload, current_user.id, taller_id)
    return InventoryItemResponse.from_model(item.repuesto, item)


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_EDITAR])),
):
    taller_id = get_user_taller_id(current_user)
    service = InventoryService(db)
    result = await service.update(item_id, payload, taller_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    
    rep, inv = result
    return InventoryItemResponse.from_model(rep, inv)


@router.post("/{item_id}/restock", response_model=InventoryItemResponse)
async def restock_item(
    item_id: int,
    payload: RestockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_AJUSTAR_STOCK])),
):
    taller_id = get_user_taller_id(current_user)
    if not taller_id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se requiere un taller asociado para reabastecer")

    service = InventoryService(db)
    result = await service.restock(item_id, payload.quantity, taller_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    
    rep, inv = result
    return InventoryItemResponse.from_model(rep, inv)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.INVENTARIO_ELIMINAR])),
):
    service = InventoryService(db)
    deleted = await service.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
