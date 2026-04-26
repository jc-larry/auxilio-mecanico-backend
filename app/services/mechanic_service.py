from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.mecanico import Mecanico
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
        result = await self.db.execute(select(func.count(Mecanico.id)))
        count = result.scalar_one()
        return f"MEC-{count + 1:04d}"

    async def _username_exists(self, username: str) -> bool:
        from app.models.usuario import Usuario
        result = await self.db.execute(select(Usuario).where(Usuario.username == username))
        return result.scalar_one_or_none() is not None

    async def create(self, data: MechanicCreate) -> Mecanico:
        from app.models.usuario import Usuario
        from app.models.rol import Rol
        from app.core.permissions import RoleEnum
        from app.core.security import hash_password

        # 1. Crear un Usuario para este mecánico
        # Generar username único a partir del nombre
        base_username = data.full_name.lower().replace(" ", "")
        username = base_username
        counter = 1
        while await self._username_exists(username):
            username = f"{base_username}{counter}"
            counter += 1
            
        # Email ficticio (requerido por el modelo)
        email = f"{username}@mail.com"
        
        user = Usuario(
            nombre=data.full_name,
            username=username,
            email=email,
            telefono=data.phone,
            hashed_password=hash_password("Mecanico123!"), # Password por defecto
            estado=True
        )
        
        # Asignar rol de Mecánico
        role_result = await self.db.execute(select(Rol).where(Rol.nombre == RoleEnum.MECANICO.value))
        role = role_result.scalar_one_or_none()
        if role:
            user.roles.append(role)
            
        self.db.add(user)
        await self.db.flush() # Para obtener el user.id
        
        # 2. Crear el registro de Mecánico
        code = await self._generate_code()
        mechanic = Mecanico(
            employee_code=code,
            usuario_id=user.id,
            taller_id=data.workshop_id,
            phone=data.phone,
            especialidad=data.specialty.value,
            expertise=data.expertise.value,
            avatar_color=data.avatar_color,
            disponible=True,
        )
        self.db.add(mechanic)
        await self.db.commit()
        await self.db.refresh(mechanic)
        
        # Cargar la relación usuario para el response
        result = await self.db.execute(
            select(Mecanico)
            .options(selectinload(Mecanico.usuario))
            .where(Mecanico.id == mechanic.id)
        )
        return result.scalars().one()

    async def get_by_id(self, mechanic_id: int) -> Mecanico | None:
        result = await self.db.execute(
            select(Mecanico)
            .options(selectinload(Mecanico.usuario))
            .where(Mecanico.id == mechanic_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        available_filter: bool | None = None,
        specialty_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[Mecanico], int]:
        query = select(Mecanico).options(selectinload(Mecanico.usuario))

        if available_filter is not None:
            query = query.where(Mecanico.disponible == available_filter)

        if specialty_filter:
            query = query.where(Mecanico.especialidad == specialty_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Mecanico.employee_code.asc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, mechanic_id: int, data: MechanicUpdate) -> Mecanico | None:
        result = await self.db.execute(
            select(Mecanico)
            .options(selectinload(Mecanico.usuario))
            .where(Mecanico.id == mechanic_id)
        )
        mechanic = result.scalar_one_or_none()
        
        if not mechanic:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Map schema fields to model fields
        field_map = {
            "specialty": "especialidad",
            "is_available": "disponible",
            "workshop_id": "taller_id",
        }

        for field, value in update_data.items():
            if value is not None:
                if hasattr(value, "value"):
                    value = value.value
                
                if field == "full_name" and mechanic.usuario:
                    mechanic.usuario.nombre = value
                else:
                    model_field = field_map.get(field, field)
                    if hasattr(mechanic, model_field):
                        setattr(mechanic, model_field, value)

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
        total_result = await self.db.execute(select(func.count(Mecanico.id)))
        total = total_result.scalar_one()

        available_result = await self.db.execute(
            select(func.count()).where(Mecanico.disponible == True)  # noqa: E712
        )
        available = available_result.scalar_one()

        # Top specialty
        all_result = await self.db.execute(select(Mecanico.especialidad))
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
