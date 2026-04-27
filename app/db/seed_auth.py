import asyncio
import logging

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.rol import Rol, Permiso
from app.models.usuario import Usuario
from app.core.permissions import RoleEnum, PermissionEnum
from app.services.user_service import UserService
from app.schemas.auth import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del Administrador inicial
EMAIL_ADMIN = "admin@example.com"
PASSWORD_ADMIN = "Admin123"

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
            RoleEnum.PROPIETARIO: [       
                # USUARIOS
                PermissionEnum.USUARIOS_VER.value,
                PermissionEnum.USUARIOS_CREAR.value,
                PermissionEnum.USUARIOS_EDITAR.value,
                PermissionEnum.USUARIOS_ELIMINAR.value,

                # SERVICIOS
                PermissionEnum.SERVICIOS_VER.value,
                PermissionEnum.SERVICIOS_CREAR.value,
                PermissionEnum.SERVICIOS_EDITAR.value,
                PermissionEnum.SERVICIOS_ELIMINAR.value,
                
                # CLIENTES
                PermissionEnum.CLIENTES_VER.value,
                PermissionEnum.CLIENTES_CREAR.value,
                PermissionEnum.CLIENTES_EDITAR.value,
                PermissionEnum.CLIENTES_ELIMINAR.value,

                # VEHÍCULOS
                PermissionEnum.VEHICULOS_VER.value,
                PermissionEnum.VEHICULOS_CREAR.value,
                PermissionEnum.VEHICULOS_EDITAR.value,
                PermissionEnum.VEHICULOS_ELIMINAR.value,
                
                # SOLICITUDES
                PermissionEnum.SOLICITUDES_VER.value,
                PermissionEnum.SOLICITUDES_CREAR.value,
                PermissionEnum.SOLICITUDES_ACEPTAR.value,
                PermissionEnum.SOLICITUDES_RECHAZAR.value,
                PermissionEnum.SOLICITUDES_ASIGNAR_MECANICO.value,
                PermissionEnum.SOLICITUDES_CAMBIAR_ESTADO.value,
      
                # INVENTARIO
                PermissionEnum.INVENTARIO_VER.value,
                PermissionEnum.INVENTARIO_AGREGAR.value,
                PermissionEnum.INVENTARIO_EDITAR.value,
                PermissionEnum.INVENTARIO_AJUSTAR_STOCK.value,
                PermissionEnum.INVENTARIO_ELIMINAR.value,
                
                # FACTURAS
                PermissionEnum.FACTURAS_VER.value,
                PermissionEnum.FACTURAS_CREAR.value,
                PermissionEnum.FACTURAS_ANULAR.value,
                
                # PAGOS
                PermissionEnum.PAGOS_VER.value,
           
                # ANALÍTICAS
                PermissionEnum.TALLERES_ANALITICAS.value,

                # TALLERES
                PermissionEnum.TALLERES_VER.value,
                PermissionEnum.TALLERES_CREAR.value,
            ],
            RoleEnum.MECANICO: [
                PermissionEnum.USUARIOS_VER.value,
                PermissionEnum.SOLICITUDES_VER.value,
                PermissionEnum.SOLICITUDES_ASIGNAR_MECANICO.value,
                PermissionEnum.SOLICITUDES_CAMBIAR_ESTADO.value,
                PermissionEnum.INVENTARIO_VER.value,
                PermissionEnum.INVENTARIO_AJUSTAR_STOCK.value,
                PermissionEnum.VEHICULOS_VER.value,
                PermissionEnum.SERVICIOS_VER.value,
            ],
            RoleEnum.CLIENTE: [
                PermissionEnum.VEHICULOS_VER.value,
                PermissionEnum.SOLICITUDES_CREAR.value,
                PermissionEnum.SOLICITUDES_VER.value,
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

        # 4. Crear usuario administrador si no existe
        service = UserService(db)
        admin_user = await service.get_by_email(EMAIL_ADMIN)
                
        if not admin_user:
            logger.info(f"Creando usuario administrador: {EMAIL_ADMIN}")
            admin_data = UserCreate(
                email=EMAIL_ADMIN,
                password=PASSWORD_ADMIN,
                confirm_password=PASSWORD_ADMIN,
                full_name="Administrador del Sistema",
                username="admin"
            )
            # UserService.create ya le asigna el rol 'Cliente' por defecto ahora,
            # pero aquí lo elevaremos a 'Administrador'
            admin_user = await service.create(admin_data)
        
        # Asegurar que tenga el rol ADMINISTRADOR
        # (cargamos roles para verificar)
        from sqlalchemy.orm import selectinload
        stmt = select(Usuario).options(selectinload(Usuario.roles)).where(Usuario.id == admin_user.id)
        result = await db.execute(stmt)
        admin_user = result.scalar_one()
        
        admin_role_name = RoleEnum.ADMINISTRADOR.value
        if not any(r.nombre == admin_role_name for r in admin_user.roles):
            admin_user.roles.append(roles_db[admin_role_name])
            await db.commit()
            logger.info(f"Se ha asignado el rol ADMINISTRADOR al usuario {admin_user.username}")
        else:
            logger.info("El usuario ya tiene el rol ADMINISTRADOR.")

        # 5. Crear tipos de servicio por defecto si no existen
        logger.info("Verificando tipos de servicio por defecto...")
        from app.models.tipo_servicio import TipoServicio
        from app.schemas.service_request import SERVICE_ICONS
        
        default_services = [
            ("Grúa / Remolque", "Servicio de grúa o remolque para vehículos averiados", 50.0),
            ("Cambio de Neumático", "Sustitución de neumáticos pinchados o dañados", 15.0),
            ("Servicio de Batería", "Recarga o cambio de batería", 20.0),
            ("Apertura de Vehículo", "Asistencia para llaves olvidadas dentro del vehículo", 30.0),
            ("Suministro de Combustible", "Entrega de combustible de emergencia", 10.0),
            ("Diagnóstico", "Diagnóstico general de fallas mecánicas", 25.0),
            ("Reparación de Frenos", "Revisión y cambio de pastillas o discos de freno", 60.0),
            ("Cambio de Aceite", "Sustitución de aceite y filtro", 40.0),
            ("Transmisión", "Revisión y mantenimiento de transmisión", 80.0),
            ("Servicio General", "Mantenimiento preventivo general", 45.0),
        ]
        
        for name, desc, price in default_services:
            result = await db.execute(select(TipoServicio).where(TipoServicio.nombre == name))
            if not result.scalar_one_or_none():
                new_tipo = TipoServicio(nombre=name, descripcion=desc, precio_base=price)
                db.add(new_tipo)
        await db.commit()
        logger.info("Tipos de servicio por defecto verificados/creados.")

if __name__ == "__main__":
    asyncio.run(seed_auth())
