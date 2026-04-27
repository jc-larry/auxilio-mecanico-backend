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
from app.services.bitacora_service import BitacoraService


class MechanicService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _email_exists(self, email: str) -> bool:
        from app.models.usuario import Usuario
        result = await self.db.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none() is not None

    async def create(self, data: MechanicCreate, taller_id: int | None = None) -> Mecanico:
        from app.models.usuario import Usuario
        from app.models.rol import Rol
        from app.core.permissions import RoleEnum
        from app.core.security import hash_password

        # 1. Crear un Usuario para este mecánico
        # Generar email único a partir del nombre
        base_email = f"{data.full_name.lower().replace(' ', '')}@mail.com"
        email = base_email
        counter = 1
        while await self._email_exists(email):
            email = f"{data.full_name.lower().replace(' ', '')}{counter}@mail.com"
            counter += 1
            
        user = Usuario(
            nombre=data.full_name,
            email=email,
            telefono=getattr(data, "phone", ""),
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
        
        mechanic = Mecanico(
            usuario_id=user.id,
            taller_id=taller_id if taller_id is not None else data.workshop_id,
            especialidad=data.specialty.value,
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
        taller_id: int | None = None,
    ) -> tuple[list[Mecanico], int]:
        query = select(Mecanico).options(selectinload(Mecanico.usuario))

        if available_filter is not None:
            query = query.where(Mecanico.disponible == available_filter)

        if specialty_filter:
            query = query.where(Mecanico.especialidad == specialty_filter)

        if taller_id is not None:
            query = query.where(Mecanico.taller_id == taller_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Mecanico.id.asc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, mechanic_id: int, data: MechanicUpdate, current_user_id: int) -> Mecanico | None:
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
        
        # Log to bitácora if availability changed
        if "is_available" in update_data:
            bitacora = BitacoraService(self.db)
            await bitacora.log_action(
                usuario_id=current_user_id,
                accion="CAMBIAR_DISPONIBILIDAD",
                entidad="Mecanico",
                entidad_id=str(mechanic.id),
                detalles={"disponible": mechanic.disponible}
            )
            await self.db.commit()
            
        return mechanic

    async def delete(self, mechanic_id: int) -> bool:
        mechanic = await self.get_by_id(mechanic_id)
        if not mechanic:
            return False
        await self.db.delete(mechanic)
        await self.db.commit()
        return True

    async def get_stats(self, taller_id: int | None = None) -> MechanicStats:
        total_query = select(func.count(Mecanico.id))
        if taller_id is not None:
            total_query = total_query.where(Mecanico.taller_id == taller_id)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        available_query = select(func.count()).where(Mecanico.disponible == True)  # noqa: E712
        if taller_id is not None:
            available_query = available_query.where(Mecanico.taller_id == taller_id)
        available_result = await self.db.execute(available_query)
        available = available_result.scalar_one()

        # Top specialty
        all_query = select(Mecanico.especialidad)
        if taller_id is not None:
            all_query = all_query.where(Mecanico.taller_id == taller_id)
        all_result = await self.db.execute(all_query)
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
