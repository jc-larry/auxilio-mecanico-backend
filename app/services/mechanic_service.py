from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mechanic import Mechanic
from app.schemas.mechanic import (
    SPECIALTY_LABELS,
    MechanicCreate,
    MechanicStats,
    MechanicUpdate,
)


class MechanicService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _generate_code(self) -> str:
        result = await self.db.execute(select(func.count(Mechanic.id)))
        count = result.scalar_one()
        return f"MEC-{count + 1:04d}"

    async def create(self, data: MechanicCreate, user_id: int) -> Mechanic:
        code = await self._generate_code()
        mechanic = Mechanic(
            employee_code=code,
            full_name=data.full_name,
            phone=data.phone,
            specialty=data.specialty.value,
            expertise=data.expertise.value,
            avatar_color=data.avatar_color,
            is_available=True,
            user_id=user_id,
        )
        self.db.add(mechanic)
        await self.db.commit()
        await self.db.refresh(mechanic)
        return mechanic

    async def get_by_id(self, mechanic_id: int) -> Mechanic | None:
        result = await self.db.execute(
            select(Mechanic).where(Mechanic.id == mechanic_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        available_filter: bool | None = None,
        specialty_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[Mechanic], int]:
        query = select(Mechanic)

        if available_filter is not None:
            query = query.where(Mechanic.is_available == available_filter)

        if specialty_filter:
            query = query.where(Mechanic.specialty == specialty_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Mechanic.full_name.asc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, mechanic_id: int, data: MechanicUpdate) -> Mechanic | None:
        mechanic = await self.get_by_id(mechanic_id)
        if not mechanic:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if hasattr(value, "value"):
                    value = value.value
                setattr(mechanic, field, value)

        mechanic.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(mechanic)
        return mechanic

    async def delete(self, mechanic_id: int) -> bool:
        mechanic = await self.get_by_id(mechanic_id)
        if not mechanic:
            return False
        await self.db.delete(mechanic)
        await self.db.commit()
        return True

    async def get_stats(self) -> MechanicStats:
        total_result = await self.db.execute(select(func.count(Mechanic.id)))
        total = total_result.scalar_one()

        available_result = await self.db.execute(
            select(func.count()).where(Mechanic.is_available == True)  # noqa: E712
        )
        available = available_result.scalar_one()

        # Top specialty
        all_result = await self.db.execute(select(Mechanic.specialty))
        specialties = [row[0] for row in all_result.all()]
        counter = Counter(specialties)
        top_spec, top_count = counter.most_common(1)[0] if counter else ("general", 0)

        return MechanicStats(
            total=total,
            available=available,
            unavailable=total - available,
            top_specialty=SPECIALTY_LABELS.get(top_spec, top_spec),
            top_specialty_count=top_count,
        )
