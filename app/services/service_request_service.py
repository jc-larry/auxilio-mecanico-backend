from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.solicitud_servicio import SolicitudServicio, HistorialEstadoSolicitud
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.tipo_servicio import TipoServicio
from app.models.mecanico import Mecanico
from app.models.taller import Taller
from app.models.enums import EstadoSolicitud
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestStats,
    ServiceRequestUpdate,
)
from app.services.bitacora_service import BitacoraService


class ServiceRequestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _generate_code(self) -> str:
        """Auto-generate sequential code like SR-0001, SR-0002... using max ID."""
        result = await self.db.execute(select(func.max(SolicitudServicio.id)))
        max_id = result.scalar() or 0
        return f"SR-{max_id + 1:04d}"

    async def _get_tipo_servicio(self, code: str) -> TipoServicio:
        """Busca tipo de servicio por nombre/código."""
        result = await self.db.execute(select(TipoServicio).where(TipoServicio.nombre == code))
        tipo = result.scalar_one_or_none()

        if not tipo:
            # Crear uno por defecto si no existe
            tipo = TipoServicio(nombre=code, descripcion=f"Servicio {code}", precio_base=0.0)
            self.db.add(tipo)
            await self.db.flush()
        
        return tipo

    async def _get_default_taller(self) -> int | None:
        result = await self.db.execute(select(Taller.id).limit(1))
        return result.scalar()

    async def create(self, data: ServiceRequestCreate, user_id: int) -> SolicitudServicio:
        tipo = await self._get_tipo_servicio(data.service_type.value)
        taller_id = await self._get_default_taller()
        codigo = await self._generate_code()

        try:
            sr = SolicitudServicio(
                codigo=codigo,
                cliente_id=data.cliente_id,
                vehiculo_id=data.vehiculo_id,
                tipo_servicio_id=tipo.id,
                taller_id=taller_id,
                descripcion_problema=data.description,
                ubicacion=data.location,
                prioridad=data.priority.value,
                estado=EstadoSolicitud.PENDIENTE,
                progreso=0,
                usuario_id=user_id,
            )
            self.db.add(sr)
            await self.db.commit()
            await self.db.refresh(sr)
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error al persistir la solicitud: {str(e)}")
        
        # Recargar con relaciones
        result = await self.db.execute(
            select(SolicitudServicio)
            .options(
                selectinload(SolicitudServicio.cliente).selectinload(Cliente.usuario),
                selectinload(SolicitudServicio.vehiculo),
                selectinload(SolicitudServicio.tipo_servicio),
                selectinload(SolicitudServicio.mecanico).selectinload(Mecanico.usuario)
            )
            .where(SolicitudServicio.id == sr.id)
        )
        return result.scalar_one()

    async def get_by_id(self, request_id: int) -> SolicitudServicio | None:
        result = await self.db.execute(
            select(SolicitudServicio)
            .options(
                selectinload(SolicitudServicio.cliente).selectinload(Cliente.usuario),
                selectinload(SolicitudServicio.vehiculo),
                selectinload(SolicitudServicio.tipo_servicio),
                selectinload(SolicitudServicio.mecanico).selectinload(Mecanico.usuario)
            )
            .where(SolicitudServicio.id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
        taller_id: int | None = None,
    ) -> tuple[list[SolicitudServicio], int]:
        query = select(SolicitudServicio).options(
            selectinload(SolicitudServicio.cliente).selectinload(Cliente.usuario),
            selectinload(SolicitudServicio.vehiculo),
            selectinload(SolicitudServicio.tipo_servicio),
            selectinload(SolicitudServicio.mecanico).selectinload(Mecanico.usuario)
        )

        if status_filter:
            # Mapeo de estados legacy -> nuevo
            status_map = {"COMPLETADO": "COMPLETADA", "RECHAZADO": "RECHAZADA"}
            new_status = status_map.get(status_filter, status_filter)
            query = query.where(SolicitudServicio.estado == new_status)

        if taller_id is not None:
            query = query.where(SolicitudServicio.taller_id == taller_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(SolicitudServicio.fecha_creacion.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, request_id: int, data: ServiceRequestUpdate, current_user_id: int) -> SolicitudServicio | None:
        sr = await self.get_by_id(request_id)
        if not sr:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data:
            status_val = update_data["status"]
            # Extraer valor string del enum si es necesario
            status_str = status_val.value if hasattr(status_val, "value") else status_val
            
            # Mapeo legacy -> nuevo
            status_map = {
                "PENDIENTE": EstadoSolicitud.PENDIENTE,
                "EN_PROGRESO": EstadoSolicitud.EN_PROGRESO,
                "CRITICO": EstadoSolicitud.CRITICO,
                "COMPLETADO": EstadoSolicitud.COMPLETADA,
                "RECHAZADO": EstadoSolicitud.RECHAZADA
            }
            
            sr.estado = status_map.get(status_str, EstadoSolicitud.PENDIENTE)
            
            if status_str == "COMPLETADO":
                sr.fecha_fin = datetime.now(timezone.utc)
                sr.progreso = 100
            else:
                sr.fecha_fin = None

        if "assigned_mechanic" in update_data and update_data["assigned_mechanic"]:
            # Buscar mecánico por nombre de usuario
            mec_name = update_data["assigned_mechanic"]
            mec_result = await self.db.execute(
                select(Mecanico)
                .join(Usuario)
                .where(Usuario.nombre == mec_name)
            )
            mechanic = mec_result.scalar_one_or_none()
            if mechanic:
                sr.mecanico_id = mechanic.id
                sr.fecha_asignacion = datetime.now(timezone.utc)

        if "progress" in update_data:
            sr.progreso = update_data["progress"]
        if "description" in update_data:
            sr.descripcion_problema = update_data["description"]
        if "priority" in update_data:
            sr.prioridad = update_data["priority"]

        await self.db.commit()
        await self.db.refresh(sr)
        
        # Log to Bitácora
        bitacora = BitacoraService(self.db)
        if "assigned_mechanic" in update_data and update_data["assigned_mechanic"]:
            await bitacora.log_action(
                usuario_id=current_user_id,
                accion="ASIGNAR_MECANICO",
                entidad="SolicitudServicio",
                entidad_id=str(sr.id),
                detalles={"mecanico_id": sr.mecanico_id, "codigo": sr.codigo}
            )
        
        if "status" in update_data:
            await bitacora.log_action(
                usuario_id=current_user_id,
                accion="ACTUALIZAR_ESTADO",
                entidad="SolicitudServicio",
                entidad_id=str(sr.id),
                detalles={"nuevo_estado": sr.estado.value, "codigo": sr.codigo}
            )
            
        await self.db.commit()
        
        return await self.get_by_id(request_id)

    async def delete(self, request_id: int) -> bool:
        sr = await self.db.get(SolicitudServicio, request_id)
        if not sr:
            return False
        await self.db.delete(sr)
        await self.db.commit()
        return True

    async def get_stats(self, taller_id: int | None = None) -> ServiceRequestStats:
        # Total en cola (no COMPLETADA ni RECHAZADA)
        active_query = select(func.count()).where(
            SolicitudServicio.estado.notin_([EstadoSolicitud.COMPLETADA, EstadoSolicitud.RECHAZADA, EstadoSolicitud.CANCELADA])
        )
        if taller_id is not None:
            active_query = active_query.where(SolicitudServicio.taller_id == taller_id)
        total_queue = (await self.db.execute(active_query)).scalar_one()

        # Críticos
        critical_query = select(func.count()).where(SolicitudServicio.estado == EstadoSolicitud.CRITICO)
        if taller_id is not None:
            critical_query = critical_query.where(SolicitudServicio.taller_id == taller_id)
        critical_count = (await self.db.execute(critical_query)).scalar_one()

        # Tasa de cierre
        total_query = select(func.count(SolicitudServicio.id))
        completed_query = select(func.count()).where(SolicitudServicio.estado == EstadoSolicitud.COMPLETADA)
        
        if taller_id is not None:
            total_query = total_query.where(SolicitudServicio.taller_id == taller_id)
            completed_query = completed_query.where(SolicitudServicio.taller_id == taller_id)

        total_all = (await self.db.execute(total_query)).scalar_one()
        completed_count = (await self.db.execute(completed_query)).scalar_one()
        
        completion_rate = (completed_count / total_all * 100) if total_all > 0 else 0.0

        # Lead time
        completed_items_query = select(SolicitudServicio).where(
            SolicitudServicio.estado == EstadoSolicitud.COMPLETADA,
            SolicitudServicio.fecha_fin.isnot(None),
        )
        if taller_id is not None:
            completed_items_query = completed_items_query.where(SolicitudServicio.taller_id == taller_id)
        completed_items = (await self.db.execute(completed_items_query)).scalars().all()
        
        avg_lead_time = 0.0
        if completed_items:
            total_hours = sum(
                (item.fecha_fin - item.fecha_creacion).total_seconds() / 3600
                for item in completed_items
            )
            avg_lead_time = round(total_hours / len(completed_items), 1)

        return ServiceRequestStats(
            total_queue=total_queue,
            avg_lead_time_hours=avg_lead_time,
            critical_count=critical_count,
            completion_rate=round(completion_rate, 1),
        )
