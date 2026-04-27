from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import and_, case, func, select
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

    async def create(self, data: InventoryItemCreate, user_id: int, taller_id: int | None = None) -> InventarioRepuesto:
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
        if taller_id:
            inventario = await self._get_inventario_by_taller(taller_id)
        else:
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
            .select_from(InventarioRepuesto)
            .join(InventarioRepuesto.repuesto)
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
        taller_id: int | None = None,
    ) -> tuple[list[tuple[Repuesto, InventarioRepuesto | None]], int]:
        # Empezar desde Repuesto para listar TODO el catálogo
        if taller_id is not None:
            # Subconsulta para obtener el ID del inventario del taller
            inv_id_subquery = select(Inventario.id).where(Inventario.taller_id == taller_id).scalar_subquery()
            
            query = select(Repuesto, InventarioRepuesto).select_from(Repuesto).outerjoin(
                InventarioRepuesto,
                and_(
                    InventarioRepuesto.repuesto_id == Repuesto.id,
                    InventarioRepuesto.inventario_id == inv_id_subquery
                )
            )
        else:
            query = select(Repuesto, InventarioRepuesto).select_from(Repuesto).outerjoin(
                InventarioRepuesto,
                (InventarioRepuesto.repuesto_id == Repuesto.id)
            )

        if category_filter:
            query = query.where(Repuesto.system_category == category_filter)

        if critical_only:
            # Solo los que tienen stock bajo o nulo
            query = query.where(
                (InventarioRepuesto.id == None) | 
                (InventarioRepuesto.cantidad <= InventarioRepuesto.min_stock)
            )

        # Contar total de repuestos
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Ordenar
        query = query.order_by(Repuesto.nombre.asc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.all())  # Lista de tuplas (Repuesto, InventarioRepuesto)

        return items, total

    async def get_by_repuesto_id(self, repuesto_id: int, taller_id: int | None = None) -> tuple[Repuesto, InventarioRepuesto | None] | None:
        rep_result = await self.db.execute(select(Repuesto).where(Repuesto.id == repuesto_id))
        repuesto = rep_result.scalar_one_or_none()
        if not repuesto:
            return None
        
        inv_item = None
        if taller_id:
            inv_result = await self.db.execute(
                select(InventarioRepuesto)
                .select_from(InventarioRepuesto)
                .join(InventarioRepuesto.inventario)
                .where(InventarioRepuesto.repuesto_id == repuesto_id)
                .where(Inventario.taller_id == taller_id)
            )
            inv_item = inv_result.scalar_one_or_none()
        
        return repuesto, inv_item

    async def update(self, repuesto_id: int, data: InventoryItemUpdate, taller_id: int | None = None) -> tuple[Repuesto, InventarioRepuesto | None] | None:
        result = await self.get_by_repuesto_id(repuesto_id, taller_id)
        if not result:
            return None
        
        repuesto, item = result
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            repuesto.nombre = update_data["name"]
        if "system_category" in update_data:
            repuesto.system_category = update_data["system_category"]
        if "unit_price" in update_data:
            repuesto.precio = Decimal(str(update_data["unit_price"]))
        
        if item:
            if "quantity" in update_data:
                item.cantidad = update_data["quantity"]
            if "min_stock" in update_data:
                item.min_stock = update_data["min_stock"]
        elif taller_id and ("quantity" in update_data or "min_stock" in update_data):
            # Si no existía en el inventario pero se está actualizando stock, crearlo
            inventario = await self._get_inventario_by_taller(taller_id)
            item = InventarioRepuesto(
                inventario_id=inventario.id,
                repuesto_id=repuesto.id,
                cantidad=update_data.get("quantity", 0),
                min_stock=update_data.get("min_stock", 5)
            )
            self.db.add(item)

        try:
            await self.db.commit()
        except Exception as e:
            import logging
            logging.error(f"Error during update commit: {e}")
            await self.db.rollback()
            raise e
        return repuesto, item

    async def restock(self, repuesto_id: int, quantity: int, taller_id: int) -> tuple[Repuesto, InventarioRepuesto] | None:
        result = await self.get_by_repuesto_id(repuesto_id, taller_id)
        if not result:
            return None
        
        repuesto, item = result
        if not item:
            # Crear entrada en el inventario si no existe
            inventario = await self._get_inventario_by_taller(taller_id)
            item = InventarioRepuesto(
                inventario_id=inventario.id,
                repuesto_id=repuesto.id,
                cantidad=quantity,
                min_stock=5
            )
            self.db.add(item)
        else:
            item.cantidad += quantity
            
        await self.db.commit()
        return repuesto, item

    async def delete(self, repuesto_id: int) -> bool:
        # Nota: Esto elimina el REPUESTO de todo el catálogo, no solo del taller
        rep_result = await self.db.execute(select(Repuesto).where(Repuesto.id == repuesto_id))
        repuesto = rep_result.scalar_one_or_none()
        if not repuesto:
            return False
        await self.db.delete(repuesto)
        await self.db.commit()
        return True

    async def _get_inventario_by_taller(self, taller_id: int) -> Inventario:
        inv_result = await self.db.execute(
            select(Inventario).where(Inventario.taller_id == taller_id)
        )
        inventario = inv_result.scalar_one_or_none()
        if not inventario:
            inventario = Inventario(taller_id=taller_id)
            self.db.add(inventario)
            await self.db.flush()
        return inventario

    async def get_stats(self, taller_id: int | None = None) -> InventoryStats:
        # Consulta consolidada para todas las estadísticas
        query = select(
            func.count(InventarioRepuesto.id).label("total_items"),
            func.coalesce(func.sum(InventarioRepuesto.cantidad), 0).label("total_units"),
            func.sum(
                case(
                    (InventarioRepuesto.cantidad <= InventarioRepuesto.min_stock, 1),
                    else_=0
                )
            ).label("critical_count"),
            func.coalesce(func.sum(InventarioRepuesto.cantidad * Repuesto.precio), 0).label("total_value")
        ).select_from(InventarioRepuesto).join(InventarioRepuesto.repuesto)
        
        if taller_id is not None:
            query = query.join(InventarioRepuesto.inventario).where(Inventario.taller_id == taller_id)
            
        result = await self.db.execute(query)
        row = result.mappings().one()
        
        return InventoryStats(
            total_items=row["total_items"] or 0,
            total_units=row["total_units"] or 0,
            critical_count=row["critical_count"] or 0,
            total_value=float(row["total_value"]),
        )
