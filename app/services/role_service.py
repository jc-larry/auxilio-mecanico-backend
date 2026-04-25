from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.rol import Rol, Permiso
from app.schemas.role import RoleCreate, RoleUpdate

class RoleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all_permissions(self) -> list[Permiso]:
        result = await self.db.execute(select(Permiso).order_by(Permiso.nombre))
        return list(result.scalars().all())

    async def get_by_id(self, role_id: int) -> Rol | None:
        result = await self.db.execute(
            select(Rol)
            .options(selectinload(Rol.permisos))
            .where(Rol.id == role_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, per_page: int = 10) -> tuple[list[Rol], int]:
        offset = (page - 1) * per_page
        query = select(Rol).options(selectinload(Rol.permisos))
        count_query = select(func.count()).select_from(Rol)
        total = await self.db.scalar(count_query) or 0
        items_result = await self.db.execute(
            query.order_by(Rol.id.desc()).offset(offset).limit(per_page)
        )
        items = list(items_result.scalars().all())
        return items, total

    async def create(self, data: RoleCreate) -> Rol:
        role = Rol(nombre=data.nombre)
        if data.permisos_ids:
            permisos_result = await self.db.execute(
                select(Permiso).where(Permiso.id.in_(data.permisos_ids))
            )
            role.permisos = list(permisos_result.scalars().all())
        
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return await self.get_by_id(role.id)

    async def update(self, role_id: int, data: RoleUpdate) -> Rol | None:
        role = await self.get_by_id(role_id)
        if not role:
            return None
        
        if data.nombre is not None:
            role.nombre = data.nombre
        
        if data.permisos_ids is not None:
            permisos_result = await self.db.execute(
                select(Permiso).where(Permiso.id.in_(data.permisos_ids))
            )
            role.permisos = list(permisos_result.scalars().all())
            
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, role_id: int) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False
        
        await self.db.delete(role)
        await self.db.commit()
        return True

    async def create_permission(self, nombre: str) -> Permiso:
        permiso = Permiso(nombre=nombre)
        self.db.add(permiso)
        await self.db.commit()
        await self.db.refresh(permiso)
        return permiso

    async def delete_permission(self, permiso_id: int) -> bool:
        result = await self.db.execute(select(Permiso).where(Permiso.id == permiso_id))
        permiso = result.scalar_one_or_none()
        if not permiso:
            return False
        await self.db.delete(permiso)
        await self.db.commit()
        return True
