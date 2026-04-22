from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.auth import UserCreate
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_permissions(self, user_id: int) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario)
            .options(selectinload(Usuario.roles).selectinload(Rol.permisos))
            .where(Usuario.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.username == username))
        return result.scalar_one_or_none()

    async def create(self, data: UserCreate) -> Usuario:
        user = Usuario(
            email=data.email,
            username=data.username,
            nombre=data.full_name,
            hashed_password=hash_password(data.password),
            estado=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> Usuario | None:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.estado:
            return None
        await self._update_last_login(user)
        return user

    async def _update_last_login(self, user: Usuario) -> None:
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()

    async def list_all(self, page: int = 1, per_page: int = 10) -> tuple[list[Usuario], int]:
        offset = (page - 1) * per_page
        
        # Base query eagerly loading roles and permissions
        query = select(Usuario).options(selectinload(Usuario.roles).selectinload(Rol.permisos))
        
        # Get total count
        count_query = select(func.count()).select_from(Usuario)
        total = await self.db.scalar(count_query) or 0
        
        # Get items
        items_result = await self.db.execute(
            query.order_by(Usuario.id.desc()).offset(offset).limit(per_page)
        )
        items = list(items_result.scalars().all())
        
        return items, total

    async def update(self, user_id: int, data: UserUpdate, current_user_id: int) -> Usuario | None:
        user = await self.get_by_id_with_permissions(user_id)
        if not user:
            return None

        if data.full_name is not None:
            user.nombre = data.full_name
            
        if data.is_active is not None:
            user.estado = data.is_active

        if data.roles is not None:
            # Only allow role modifications if not modifying self
            if user_id != current_user_id:
                # Fetch roles by name with permissions eagerly loaded
                roles_query = await self.db.execute(
                    select(Rol)
                    .options(selectinload(Rol.permisos))
                    .where(Rol.nombre.in_(data.roles))
                )
                db_roles = roles_query.scalars().all()
                user.roles = list(db_roles)

        await self.db.commit()
        await self.db.refresh(user)
        return user
