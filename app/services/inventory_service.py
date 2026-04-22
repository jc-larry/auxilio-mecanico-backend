from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventario import Inventario, InventarioRepuesto
from app.models.repuesto import Repuesto
from app.models.taller import Taller
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryStats,
)


class InventoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_default_inventario(self) -> Inventario:
        """Obtiene o crea un inventario por defecto (asociado al primer taller)."""
        # Intentar obtener el primer taller
        taller_result = await self.db.execute(select(Taller).limit(1))
        taller = taller_result.scalar_one_or_none()

        if not taller:
            # Crear un taller por defecto si no existe ninguno (para evitar errores en la migración)
            taller = Taller(
                nombre="Taller Central",
                direccion="Calle Principal 123",
                latitud=0.0,
                longitud=0.0,
                telefono="555-0100"
            )
            self.db.add(taller)
            await self.db.flush()

        # Buscar inventario para este taller
        inv_result = await self.db.execute(
            select(Inventario).where(Inventario.taller_id == taller.id)
        )
        inventario = inv_result.scalar_one_or_none()

        if not inventario:
            inventario = Inventario(taller_id=taller.id)
            self.db.add(inventario)
            await self.db.flush()

        return inventario

    async def create(self, data: InventoryItemCreate, user_id: int) -> InventarioRepuesto:
        # 1. Buscar o crear el Repuesto por SKU
        rep_result = await self.db.execute(
            select(Repuesto).where(Repuesto.sku == data.sku)
        )
        repuesto = rep_result.scalar_one_or_none()

        if not repuesto:
            repuesto = Repuesto(
                sku=data.sku,
                nombre=data.name,
                system_category=data.system_category.value,
                precio=Decimal(str(data.unit_price)),
                descripcion=f"Repuesto: {data.name}"
            )
            self.db.add(repuesto)
            await self.db.flush()

        # 2. Obtener inventario del taller
        inventario = await self._get_default_inventario()

        # 3. Crear el item en el inventario
        item = InventarioRepuesto(
            inventario_id=inventario.id,
            repuesto_id=repuesto.id,
            cantidad=data.quantity,
            min_stock=data.min_stock
        )
        self.db.add(item)
        await self.db.commit()
        
        # Recargar con relaciones
        result = await self.db.execute(
            select(InventarioRepuesto)
            .options(selectinload(InventarioRepuesto.repuesto))
            .where(InventarioRepuesto.id == item.id)
        )
        return result.scalar_one()

    async def get_by_id(self, item_id: int) -> InventarioRepuesto | None:
        result = await self.db.execute(
            select(InventarioRepuesto)
            .options(selectinload(InventarioRepuesto.repuesto))
            .where(InventarioRepuesto.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> InventarioRepuesto | None:
        result = await self.db.execute(
            select(InventarioRepuesto)
            .join(Repuesto)
            .options(selectinload(InventarioRepuesto.repuesto))
            .where(Repuesto.sku == sku)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        critical_only: bool = False,
        category_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[InventarioRepuesto], int]:
        query = select(InventarioRepuesto).join(Repuesto).options(selectinload(InventarioRepuesto.repuesto))

        if critical_only:
            query = query.where(InventarioRepuesto.cantidad <= InventarioRepuesto.min_stock)

        if category_filter:
            query = query.where(Repuesto.system_category == category_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Ordenar: críticos primero, luego por nombre
        query = query.order_by(
            (InventarioRepuesto.cantidad <= InventarioRepuesto.min_stock).desc(),
            Repuesto.nombre.asc()
        )
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, item_id: int, data: InventoryItemUpdate) -> InventarioRepuesto | None:
        item = await self.get_by_id(item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        repuesto = item.repuesto

        if "name" in update_data:
            repuesto.nombre = update_data["name"]
        if "system_category" in update_data:
            repuesto.system_category = update_data["system_category"]
        if "unit_price" in update_data:
            repuesto.precio = Decimal(str(update_data["unit_price"]))
        
        if "quantity" in update_data:
            item.cantidad = update_data["quantity"]
        if "min_stock" in update_data:
            item.min_stock = update_data["min_stock"]

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def restock(self, item_id: int, quantity: int) -> InventarioRepuesto | None:
        item = await self.get_by_id(item_id)
        if not item:
            return None

        item.cantidad += quantity
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
        # Total de items (repuestos distintos en inventarios)
        total_result = await self.db.execute(select(func.count(InventarioRepuesto.id)))
        total_items = total_result.scalar_one()

        # Total de unidades
        units_result = await self.db.execute(select(func.coalesce(func.sum(InventarioRepuesto.cantidad), 0)))
        total_units = units_result.scalar_one()

        # Stock crítico
        critical_result = await self.db.execute(
            select(func.count()).where(InventarioRepuesto.cantidad <= InventarioRepuesto.min_stock)
        )
        critical_count = critical_result.scalar_one()

        # Valor total
        # Unir con repuesto para obtener precios
        value_query = select(func.sum(InventarioRepuesto.cantidad * Repuesto.precio)).join(Repuesto)
        value_result = await self.db.execute(value_query)
        total_value = value_result.scalar() or 0.0

        return InventoryStats(
            total_items=total_items,
            total_units=total_units,
            critical_count=critical_count,
            total_value=float(total_value),
        )
