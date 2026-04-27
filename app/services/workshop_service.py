from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.taller import Taller
from app.schemas.workshop import WorkshopCreate, WorkshopUpdate

class WorkshopService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, workshop_id: int) -> Taller | None:
        result = await self.db.execute(select(Taller).where(Taller.id == workshop_id))
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, per_page: int = 10, propietario_id: int | None = None) -> tuple[list[Taller], int]:
        offset = (page - 1) * per_page
        query = select(Taller)
        
        if propietario_id is not None:
            query = query.where(Taller.propietario_id == propietario_id)
            
        query = query.order_by(Taller.id.desc())
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        result = await self.db.execute(query.offset(offset).limit(per_page))
        items = list(result.scalars().all())
        
        return items, total

    async def create(self, data: WorkshopCreate, propietario_id: int | None = None) -> Taller:
        workshop_data = data.model_dump()
        if propietario_id is not None:
            workshop_data["propietario_id"] = propietario_id
            
        workshop = Taller(**workshop_data)
        self.db.add(workshop)
        await self.db.commit()
        await self.db.refresh(workshop)
        return workshop

    async def update(self, workshop_id: int, data: WorkshopUpdate) -> Taller | None:
        workshop = await self.get_by_id(workshop_id)
        if not workshop:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(workshop, key, value)
            
        await self.db.commit()
        await self.db.refresh(workshop)
        return workshop

    async def delete(self, workshop_id: int) -> bool:
        workshop = await self.get_by_id(workshop_id)
        if not workshop:
            return False
        await self.db.delete(workshop)
        await self.db.commit()
        return True
