import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryStats,
    PaginatedResponse,
    RestockRequest,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=PaginatedResponse[InventoryItemResponse])
async def list_inventory(
    critical: bool = Query(False),
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InventoryService(db)
    items, total = await service.list_all(critical, category, page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1

    return PaginatedResponse(
        items=[InventoryItemResponse.from_model(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/stats", response_model=InventoryStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InventoryService(db)
    return await service.get_stats()


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InventoryService(db)
    item = await service.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    return InventoryItemResponse.from_model(item)


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InventoryService(db)
    existing = await service.get_by_sku(payload.sku)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU ya existe")
    item = await service.create(payload, current_user.id)
    return InventoryItemResponse.from_model(item)


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_item(
    item_id: int,
    payload: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InventoryService(db)
    item = await service.update(item_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    return InventoryItemResponse.from_model(item)


@router.post("/{item_id}/restock", response_model=InventoryItemResponse)
async def restock_item(
    item_id: int,
    payload: RestockRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InventoryService(db)
    item = await service.restock(item_id, payload.quantity)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    return InventoryItemResponse.from_model(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = InventoryService(db)
    deleted = await service.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
