from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, verify_password
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.propietario import Propietario
from app.schemas.auth import UserCreate
from app.schemas.user import UserUpdate
from app.services.bitacora_service import BitacoraService


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_permissions(self, user_id: int) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario)
            .options(
                selectinload(Usuario.roles).selectinload(Rol.permisos),
                selectinload(Usuario.mecanico),
                selectinload(Usuario.propietario).selectinload(Propietario.talleres)
            )
            .where(Usuario.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()


    async def create(self, data: UserCreate) -> Usuario:
        user = Usuario(
            email=data.email,
            nombre=data.full_name,
            hashed_password=hash_password(data.password),
            estado=True,
        )
        
        # Asignar rol por defecto (Cliente)
        from app.core.permissions import RoleEnum
        role_result = await self.db.execute(
            select(Rol).where(Rol.nombre == RoleEnum.CLIENTE.value)
        )
        default_role = role_result.scalar_one_or_none()
        if default_role:
            user.roles.append(default_role)

        self.db.add(user)
        await self.db.flush()

        from app.models.cliente import Cliente
        new_client = Cliente(usuario_id=user.id)
        self.db.add(new_client)

        await self.db.commit()
        
        # Registro en Bitácora
        bitacora = BitacoraService(self.db)
        await bitacora.log_action(
            usuario_id=user.id, # Asumimos auto-registro si no hay current_user
            accion="NUEVO_USUARIO",
            entidad="Usuario",
            entidad_id=str(user.id),
            detalles={"email": user.email, "roles": [r.nombre for r in user.roles]}
        )
        await self.db.commit()
        
        # Retornar el usuario con roles y permisos cargados para evitar errores de lazy loading
        return await self.get_by_id_with_permissions(user.id)


    async def authenticate(self, email: str, password: str) -> Usuario | None:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.estado:
            return None
        return user

    async def list_all(self, page: int = 1, per_page: int = 10) -> tuple[list[Usuario], int]:
        offset = (page - 1) * per_page
        
        # Base query eagerly loading roles and permissions
        query = select(Usuario).options(
            selectinload(Usuario.roles).selectinload(Rol.permisos),
            selectinload(Usuario.mecanico),
            selectinload(Usuario.propietario).selectinload(Propietario.talleres)
        )
        
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
        
        # Registro en Bitácora para desactivación/activación
        if data.is_active is not None:
            accion = "ACTIVAR_USUARIO" if data.is_active else "DESACTIVAR_USUARIO"
            bitacora = BitacoraService(self.db)
            await bitacora.log_action(
                usuario_id=current_user_id,
                accion=accion,
                entidad="Usuario",
                entidad_id=str(user.id),
                detalles={"email": user.email}
            )
            await self.db.commit()
            
        return await self.get_by_id_with_permissions(user_id)


    async def change_password(self, user_id: int, new_password: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.hashed_password = hash_password(new_password)
        await self.db.commit()
        return True
