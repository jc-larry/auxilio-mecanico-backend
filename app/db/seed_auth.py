import asyncio
import logging

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.rol import Rol, Permiso
from app.models.usuario import Usuario
from app.core.permissions import RoleEnum, PermissionEnum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_auth():
    async with AsyncSessionLocal() as db:
        logger.info("Verificando permisos...")
        
        # 1. Crear todos los permisos
        permisos_db = {}
        for perm in PermissionEnum:
            stmt = select(Permiso).where(Permiso.nombre == perm.value)
            result = await db.execute(stmt)
            permiso = result.scalar_one_or_none()
            
            if not permiso:
                permiso = Permiso(nombre=perm.value)
                db.add(permiso)
            
            permisos_db[perm.value] = permiso
            
        await db.commit()
        
        # Asegurarse de tener las instancias actualizadas
        for perm_name, permiso in permisos_db.items():
            await db.refresh(permiso)
            
        logger.info("Permisos verificados/creados.")
        
        # 2. Definir mapa de roles a permisos
        roles_config = {
            RoleEnum.ADMINISTRADOR: [p.value for p in PermissionEnum],
            RoleEnum.SUPERVISOR: [
                p.value for p in PermissionEnum 
                if p not in (
                    PermissionEnum.USUARIOS_ELIMINAR, 
                    PermissionEnum.USUARIOS_ASIGNAR_ROL,
                    PermissionEnum.INVENTARIO_ELIMINAR,
                    PermissionEnum.ORDENES_ELIMINAR
                )
            ],
            RoleEnum.MECANICO: [
                PermissionEnum.ORDENES_VER.value,
                PermissionEnum.ORDENES_EDITAR.value,
                PermissionEnum.ORDENES_CAMBIAR_ESTADO.value,
                PermissionEnum.INVENTARIO_VER.value,
                PermissionEnum.INVENTARIO_AJUSTAR_STOCK.value,
                PermissionEnum.VEHICULOS_VER.value,
            ],
            RoleEnum.CLIENTE: [
                PermissionEnum.VEHICULOS_VER.value,
                PermissionEnum.SOLICITUDES_CREAR.value,
                PermissionEnum.SOLICITUDES_VER.value,
                PermissionEnum.SOLICITUDES_REPROGRAMAR.value,
                PermissionEnum.ORDENES_VER.value,
            ]
        }
        
        # 3. Crear roles y asignar permisos
        logger.info("Verificando roles...")
        from sqlalchemy.orm import selectinload
        roles_db = {}
        for role_enum, perms in roles_config.items():
            stmt = select(Rol).options(selectinload(Rol.permisos)).where(Rol.nombre == role_enum.value)
            result = await db.execute(stmt)
            rol = result.scalar_one_or_none()
            
            if not rol:
                rol = Rol(nombre=role_enum.value)
                db.add(rol)
                await db.commit()
                await db.refresh(rol)
                
                # Fetch again with relationships loaded
                stmt = select(Rol).options(selectinload(Rol.permisos)).where(Rol.id == rol.id)
                result = await db.execute(stmt)
                rol = result.scalar_one_or_none()
            
            # Limpiar y reasignar permisos para asegurar sincronía
            rol.permisos = [permisos_db[p] for p in perms]
            roles_db[role_enum.value] = rol
            
        await db.commit()
        logger.info("Roles y permisos asignados correctamente.")
        
        # 4. Asignar rol ADMINISTRADOR al primer usuario (si existe y no tiene roles)
        result = await db.execute(select(Usuario).order_by(Usuario.id).limit(1))
        first_user = result.scalar_one_or_none()
        
        if first_user:
            # cargar sus roles (la relación no se carga por defecto)
            from sqlalchemy.orm import selectinload
            stmt = select(Usuario).options(selectinload(Usuario.roles)).where(Usuario.id == first_user.id)
            result = await db.execute(stmt)
            first_user = result.scalar_one_or_none()
            
            if not first_user.roles:
                first_user.roles.append(roles_db[RoleEnum.ADMINISTRADOR.value])
                await db.commit()
                logger.info(f"Se ha asignado el rol ADMINISTRADOR al usuario {first_user.username}")
        else:
            logger.info("No hay usuarios en la base de datos todavía. Recuerda asignar el rol cuando crees el primero.")

if __name__ == "__main__":
    asyncio.run(seed_auth())
