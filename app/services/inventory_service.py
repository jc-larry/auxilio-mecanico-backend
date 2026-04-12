from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryStats,
)


class InventoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: InventoryItemCreate, user_id: int) -> InventoryItem:
        item = InventoryItem(
            sku=data.sku,
            name=data.name,
            system_category=data.system_category.value,
            icon="build",
            quantity=data.quantity,
            min_stock=data.min_stock,
            unit_price=data.unit_price,
            is_critical=data.quantity <= data.min_stock,
            user_id=user_id,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_by_id(self, item_id: int) -> InventoryItem | None:
        result = await self.db.execute(
            select(InventoryItem).where(InventoryItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> InventoryItem | None:
        result = await self.db.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        critical_only: bool = False,
        category_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[InventoryItem], int]:
        query = select(InventoryItem)

        if critical_only:
            query = query.where(InventoryItem.is_critical == True)  # noqa: E712

        if category_filter:
            query = query.where(InventoryItem.system_category == category_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(InventoryItem.is_critical.desc(), InventoryItem.name.asc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, item_id: int, data: InventoryItemUpdate) -> InventoryItem | None:
        item = await self.get_by_id(item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if hasattr(value, "value"):
                    value = value.value
                setattr(item, field, value)

        # Recalculate critical flag
        item.is_critical = item.quantity <= item.min_stock
        item.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def restock(self, item_id: int, quantity: int) -> InventoryItem | None:
        item = await self.get_by_id(item_id)
        if not item:
            return None

        item.quantity += quantity
        item.is_critical = item.quantity <= item.min_stock
        item.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item_id: int) -> bool:
        item = await self.get_by_id(item_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    async def get_stats(self) -> InventoryStats:
        total_result = await self.db.execute(select(func.count(InventoryItem.id)))
        total_items = total_result.scalar_one()

        units_result = await self.db.execute(select(func.coalesce(func.sum(InventoryItem.quantity), 0)))
        total_units = units_result.scalar_one()

        critical_result = await self.db.execute(
            select(func.count()).where(InventoryItem.is_critical == True)  # noqa: E712
        )
        critical_count = critical_result.scalar_one()

        # Total inventory value
        all_items_result = await self.db.execute(select(InventoryItem))
        all_items = list(all_items_result.scalars().all())
        total_value = sum(i.quantity * i.unit_price for i in all_items)

        return InventoryStats(
            total_items=total_items,
            total_units=total_units,
            critical_count=critical_count,
            total_value=round(total_value, 2),
        )
