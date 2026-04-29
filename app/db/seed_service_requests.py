import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.cliente import Cliente
from app.models.mecanico import Mecanico
from app.models.vehiculo import Vehiculo
from app.models.taller import Taller
from app.models.tipo_servicio import TipoServicio
from app.models.solicitud_servicio import SolicitudServicio, HistorialEstadoSolicitud
from app.models.enums import EstadoSolicitud
from app.core.permissions import RoleEnum
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_or_create_user(db, email, full_name, role_name):
    stmt = select(Usuario).where(Usuario.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        logger.info(f"Creando usuario: {email}")
        user = Usuario(
            nombre=full_name,
            email=email,
            hashed_password=hash_password("Test1234"),
            estado=True
        )
        db.add(user)
        await db.flush()
        
        # Asignar rol
        stmt_role = select(Rol).where(Rol.nombre == role_name)
        result_role = await db.execute(stmt_role)
        rol = result_role.scalar_one_or_none()
        if rol:
            from app.models.rol import usuario_roles
            await db.execute(usuario_roles.insert().values(usuario_id=user.id, rol_id=rol.id))
            
    return user

async def seed_service_requests():
    async with AsyncSessionLocal() as db:
        logger.info("Iniciando seed de Solicitudes de Servicio...")
        
        # 1. Obtener talleres y tipos de servicio existentes
        result_talleres = await db.execute(select(Taller))
        talleres = result_talleres.scalars().all()
        
        if not talleres:
            logger.error("No hay talleres en la base de datos. Corre seed_workshops.py primero.")
            return

        result_tipos = await db.execute(select(TipoServicio))
        tipos_servicio = result_tipos.scalars().all()
        
        if not tipos_servicio:
            logger.error("No hay tipos de servicio en la base de datos. Corre seed_auth.py primero.")
            return

        # 2. Crear Clientes
        clientes_data = [
            ("juan.perez@example.com", "Juan Pérez"),
            ("maria.garcia@example.com", "María García"),
            ("carlos.rodriguez@example.com", "Carlos Rodríguez")
        ]
        
        clientes_db = []
        for email, name in clientes_data:
            user = await get_or_create_user(db, email, name, RoleEnum.CLIENTE.value)
            
            stmt_cliente = select(Cliente).where(Cliente.usuario_id == user.id)
            result_cliente = await db.execute(stmt_cliente)
            cliente = result_cliente.scalar_one_or_none()
            
            if not cliente:
                cliente = Cliente(usuario_id=user.id)
                db.add(cliente)
                await db.flush()
            
            clientes_db.append(cliente)

        # 3. Crear Vehículos para los clientes
        vehiculos_data = [
            {"marca": "Toyota", "modelo": "Corolla", "placa": "1234-ABC", "anio": 2020, "color": "Blanco"},
            {"marca": "Suzuki", "modelo": "Grand Vitara", "placa": "5678-DEF", "anio": 2018, "color": "Gris"},
            {"marca": "Nissan", "modelo": "Sentra", "placa": "9012-GHI", "anio": 2022, "color": "Azul"},
            {"marca": "Honda", "modelo": "Civic", "placa": "3456-JKL", "anio": 2015, "color": "Rojo"},
        ]
        
        vehiculos_db = []
        for i, v_data in enumerate(vehiculos_data):
            cliente = clientes_db[i % len(clientes_db)]
            stmt_v = select(Vehiculo).where(Vehiculo.placa == v_data["placa"])
            result_v = await db.execute(stmt_v)
            vehiculo = result_v.scalar_one_or_none()
            
            if not vehiculo:
                vehiculo = Vehiculo(cliente_id=cliente.id, **v_data)
                db.add(vehiculo)
                await db.flush()
            vehiculos_db.append(vehiculo)

        # 4. Crear Mecánicos asociados a talleres
        mecanicos_data = [
            ("mecanico1@example.com", "Pedro Mecánico", "Motor"),
            ("mecanico2@example.com", "Luis Taller", "Electricidad"),
        ]
        
        mecanicos_db = []
        for email, name, esp in mecanicos_data:
            user = await get_or_create_user(db, email, name, RoleEnum.MECANICO.value)
            
            stmt_m = select(Mecanico).where(Mecanico.usuario_id == user.id)
            result_m = await db.execute(stmt_m)
            mecanico = result_m.scalar_one_or_none()
            
            if not mecanico:
                mecanico = Mecanico(
                    usuario_id=user.id,
                    taller_id=talleres[0].id,
                    especialidad=esp,
                    disponible=True
                )
                db.add(mecanico)
                await db.flush()
            mecanicos_db.append(mecanico)

        # 5. Crear Solicitudes de Servicio
        logger.info("Creando solicitudes de muestra...")
        
        solicitudes_config = [
            {
                "codigo": "SOL-001",
                "estado": EstadoSolicitud.PENDIENTE,
                "descripcion": "El auto no arranca, parece ser la batería.",
                "ubicacion": "Av. San Martín y 3er Anillo",
                "prioridad": "alta",
                "tipo_idx": 2, # Servicio de Batería
            },
            {
                "codigo": "SOL-002",
                "estado": EstadoSolicitud.EN_PROGRESO,
                "descripcion": "Cambio de neumático delantero derecho.",
                "ubicacion": "Calle Libertad #45",
                "prioridad": "media",
                "tipo_idx": 1, # Cambio de Neumático
                "mecanico_idx": 0,
                "taller_idx": 0,
            },
            {
                "codigo": "SOL-003",
                "estado": EstadoSolicitud.COMPLETADA,
                "descripcion": "Necesito una grúa, motor sobrecalentado.",
                "ubicacion": "Carretera al Norte km 10",
                "prioridad": "crítica",
                "tipo_idx": 0, # Grúa
                "mecanico_idx": 1,
                "taller_idx": 1 if len(talleres) > 1 else 0,
            }
        ]

        for s_conf in solicitudes_config:
            stmt_s = select(SolicitudServicio).where(SolicitudServicio.codigo == s_conf["codigo"])
            result_s = await db.execute(stmt_s)
            if result_s.scalar_one_or_none():
                continue
                
            vehiculo = random.choice(vehiculos_db)
            cliente = vehiculos_db[0].cliente # Usamos el dueño del vehículo
            # Buscamos el cliente_id real
            stmt_c = select(Cliente).where(Cliente.id == vehiculo.cliente_id)
            res_c = await db.execute(stmt_c)
            cliente = res_c.scalar_one()

            solicitud = SolicitudServicio(
                codigo=s_conf["codigo"],
                cliente_id=cliente.id,
                usuario_id=cliente.usuario_id, # Retrocompatibilidad
                vehiculo_id=vehiculo.id,
                tipo_servicio_id=tipos_servicio[s_conf["tipo_idx"]].id,
                estado=s_conf["estado"],
                descripcion_problema=s_conf["descripcion"],
                ubicacion=s_conf["ubicacion"],
                prioridad=s_conf["prioridad"],
                taller_id=talleres[s_conf["taller_idx"]].id if "taller_idx" in s_conf else None,
                mecanico_id=mecanicos_db[s_conf["mecanico_idx"]].id if "mecanico_idx" in s_conf else None,
                fecha_creacion=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 5)),
                progreso=100 if s_conf["estado"] == EstadoSolicitud.COMPLETADA else (50 if s_conf["estado"] == EstadoSolicitud.EN_PROGRESO else 0)
            )
            
            if s_conf["estado"] in [EstadoSolicitud.EN_PROGRESO, EstadoSolicitud.COMPLETADA]:
                solicitud.fecha_asignacion = solicitud.fecha_creacion + timedelta(minutes=30)
                solicitud.fecha_inicio = solicitud.fecha_asignacion + timedelta(minutes=15)
            
            if s_conf["estado"] == EstadoSolicitud.COMPLETADA:
                solicitud.fecha_fin = solicitud.fecha_inicio + timedelta(hours=1)

            db.add(solicitud)
            await db.flush()
            
            # Historial
            historial = HistorialEstadoSolicitud(
                solicitud_id=solicitud.id,
                estado=s_conf["estado"],
                observacion="Estado inicial del seed"
            )
            db.add(historial)
            
            logger.info(f"Creada solicitud: {solicitud.codigo}")

        await db.commit()
        logger.info("Seed de Solicitudes de Servicio completado.")

if __name__ == "__main__":
    asyncio.run(seed_service_requests())
