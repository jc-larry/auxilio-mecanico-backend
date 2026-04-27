import math
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tipo_servicio import TipoServicio
from app.schemas.service_type import TipoServicioCreate, TipoServicioUpdate

class ServiceTypeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, service_type_id: int) -> TipoServicio | None:
        result = await self.db.execute(select(TipoServicio).where(TipoServicio.id == service_type_id))
        return result.scalar_one_or_none()

    async def get_by_nombre(self, nombre: str) -> TipoServicio | None:
        result = await self.db.execute(select(TipoServicio).where(TipoServicio.nombre == nombre))
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, per_page: int = 10) -> tuple[list[TipoServicio], int, int]:
        offset = (page - 1) * per_page
        
        # Total count
        total = await self.db.scalar(select(func.count(TipoServicio.id))) or 0
        pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Items
        result = await self.db.execute(
            select(TipoServicio)
            .order_by(TipoServicio.nombre)
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        
        return items, total, pages

    async def create(self, data: TipoServicioCreate) -> TipoServicio:
        new_st = TipoServicio(
            nombre=data.nombre,
            descripcion=data.descripcion,
            precio_base=data.precio_base
        )
        self.db.add(new_st)
        await self.db.commit()
        await self.db.refresh(new_st)
        return new_st

    async def update(self, service_type_id: int, data: TipoServicioUpdate) -> TipoServicio | None:
        st = await self.get_by_id(service_type_id)
        if not st:
            return None
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(st, key, value)
            
        await self.db.commit()
        await self.db.refresh(st)
        return st

    async def delete(self, service_type_id: int) -> bool:
        st = await self.get_by_id(service_type_id)
        if not st:
            return False
            
        await self.db.delete(st)
        await self.db.commit()
        return True
