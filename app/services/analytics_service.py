from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventario import Inventario, InventarioRepuesto
from app.models.repuesto import Repuesto
from app.models.mecanico import Mecanico
from app.models.solicitud_servicio import SolicitudServicio
from app.models.tipo_servicio import TipoServicio
from app.models.usuario import Usuario
from app.models.enums import EstadoSolicitud
from app.schemas.inventory import SYSTEM_LABELS
from app.schemas.service_request import SERVICE_LABELS


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_dashboard_analytics(self, taller_id: int | None = None) -> dict:
        """Aggregate analytics data from all modules."""
        return {
            "requests_by_day": await self._requests_by_day(taller_id),
            "requests_by_type": await self._requests_by_type(taller_id),
            "requests_by_status": await self._requests_by_status(taller_id),
            "mechanic_workload": await self._mechanic_workload(taller_id),
            "inventory_by_system": await self._inventory_by_system(taller_id),
            "summary": await self._summary(taller_id),
        }

    async def _requests_by_day(self, taller_id: int | None = None) -> list[dict]:
        """Service requests per day for the last 7 days."""
        now = datetime.now(timezone.utc)
        days = []

        for i in range(6, -1, -1):
            target_date = now - timedelta(days=i)
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            query = select(func.count()).select_from(SolicitudServicio).where(
                SolicitudServicio.fecha_creacion >= day_start,
                SolicitudServicio.fecha_creacion <= day_end,
            )
            if taller_id:
                query = query.where(SolicitudServicio.taller_id == taller_id)

            result = await self.db.execute(query)
            count = result.scalar_one()

            day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            day_label = day_names[target_date.weekday()]

            days.append({
                "day": day_label,
                "value": count,
                "date": target_date.strftime("%Y-%m-%d"),
            })

        # Calculate percentages for bar heights
        max_val = max((d["value"] for d in days), default=1) or 1
        for d in days:
            d["height_pct"] = round((d["value"] / max_val) * 100)
            d["is_peak"] = d["value"] == max_val and d["value"] > 0

        return days

    async def _requests_by_type(self, taller_id: int | None = None) -> list[dict]:
        """Distribution of service requests by type."""
        query = select(TipoServicio.nombre).join(
            SolicitudServicio, SolicitudServicio.tipo_servicio_id == TipoServicio.id
        )
        if taller_id:
            query = query.where(SolicitudServicio.taller_id == taller_id)

        result = await self.db.execute(query)
        types = [row[0] for row in result.all()]
        total = len(types) or 1

        counter = Counter(types)
        colors = [
            "#091426", "#9d4300", "#d8e3fb", "#3c475a", "#1e293b",
            "#4a2c6e", "#1a4731", "#6b2130", "#2c3e50", "#7c4a03",
        ]

        items = []
        for i, (stype, count) in enumerate(counter.most_common()):
            items.append({
                "type": stype,
                "label": SERVICE_LABELS.get(stype, stype),
                "count": count,
                "pct": round(count / total * 100),
                "color": colors[i % len(colors)],
            })

        return items

    async def _requests_by_status(self, taller_id: int | None = None) -> list[dict]:
        """Count of requests per status."""
        statuses = ["PENDIENTE", "EN_PROGRESO", "CRITICO", "COMPLETADO", "RECHAZADO"]
        status_map = {
            "PENDIENTE": EstadoSolicitud.PENDIENTE,
            "EN_PROGRESO": EstadoSolicitud.EN_PROGRESO,
            "CRITICO": EstadoSolicitud.CRITICO,
            "COMPLETADO": EstadoSolicitud.COMPLETADA,
            "RECHAZADO": EstadoSolicitud.RECHAZADA,
        }
        status_labels = {
            "PENDIENTE": "Pendiente",
            "EN_PROGRESO": "En Progreso",
            "CRITICO": "Crítico",
            "COMPLETADO": "Completado",
            "RECHAZADO": "Rechazado",
        }
        status_colors = {
            "PENDIENTE": "#94a3b8",
            "EN_PROGRESO": "#fd761a",
            "CRITICO": "#ff5250",
            "COMPLETADO": "#10b981",
            "RECHAZADO": "#ef4444",
        }

        items = []
        for s in statuses:
            new_status = status_map.get(s)
            query = select(func.count()).select_from(SolicitudServicio).where(SolicitudServicio.estado == new_status)
            if taller_id:
                query = query.where(SolicitudServicio.taller_id == taller_id)

            result = await self.db.execute(query)
            count = result.scalar_one()
            items.append({
                "status": s,
                "label": status_labels.get(s, s),
                "count": count,
                "color": status_colors.get(s, "#94a3b8"),
            })

        return items

    async def _mechanic_workload(self, taller_id: int | None = None) -> list[dict]:
        """How many assigned requests per mechanic."""
        query = select(Usuario.nombre, func.count(SolicitudServicio.id))
        query = query.join(Mecanico, Mecanico.usuario_id == Usuario.id)
        query = query.join(SolicitudServicio, SolicitudServicio.mecanico_id == Mecanico.id)
        query = query.where(SolicitudServicio.estado.notin_([EstadoSolicitud.COMPLETADA, EstadoSolicitud.RECHAZADA]))
        
        if taller_id:
            query = query.where(SolicitudServicio.taller_id == taller_id)
        
        query = query.group_by(Usuario.nombre)
        
        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for name, count in rows:
            initials = "".join([n[0] for n in name.split() if n])[:2].upper() if name else "?"
            items.append({
                "name": name,
                "initials": initials,
                "assigned_count": count,
            })

        return items

    async def _inventory_by_system(self, taller_id: int | None = None) -> list[dict]:
        """Inventory units grouped by system category."""
        query = select(
            Repuesto.system_category,
            func.sum(InventarioRepuesto.cantidad),
            func.count(InventarioRepuesto.id),
        ).join(InventarioRepuesto, InventarioRepuesto.repuesto_id == Repuesto.id)
        
        if taller_id:
            query = query.join(Inventario, Inventario.id == InventarioRepuesto.inventario_id)
            query = query.where(Inventario.taller_id == taller_id)
            
        query = query.group_by(Repuesto.system_category)
        
        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for category, total_qty, item_count in rows:
            items.append({
                "category": category,
                "label": SYSTEM_LABELS.get(category, category),
                "total_units": total_qty or 0,
                "item_count": item_count,
            })

        items.sort(key=lambda x: x["total_units"], reverse=True)
        return items

    async def _summary(self, taller_id: int | None = None) -> dict:
        """High-level summary counters."""
        # Solicitudes
        q_total = select(func.count(SolicitudServicio.id))
        q_comp = select(func.count(SolicitudServicio.id)).where(SolicitudServicio.estado == EstadoSolicitud.COMPLETADA)
        q_act = select(func.count(SolicitudServicio.id)).where(SolicitudServicio.estado.notin_([EstadoSolicitud.COMPLETADA, EstadoSolicitud.RECHAZADA]))

        if taller_id:
            q_total = q_total.where(SolicitudServicio.taller_id == taller_id)
            q_comp = q_comp.where(SolicitudServicio.taller_id == taller_id)
            q_act = q_act.where(SolicitudServicio.taller_id == taller_id)

        total_requests = (await self.db.execute(q_total)).scalar_one()
        completed_requests = (await self.db.execute(q_comp)).scalar_one()
        active_requests = (await self.db.execute(q_act)).scalar_one()

        # Mecánicos
        total_mechanics = (await self.db.execute(select(func.count(Mecanico.id)))).scalar_one()
        available_mechanics = (await self.db.execute(
            select(func.count(Mecanico.id)).where(Mecanico.disponible == True)  # noqa: E712
        )).scalar_one()

        # Repuestos
        q_parts = select(func.count(InventarioRepuesto.id))
        q_crit = select(func.count(InventarioRepuesto.id)).where(InventarioRepuesto.cantidad <= InventarioRepuesto.min_stock)
        q_val = select(InventarioRepuesto).options(selectinload(InventarioRepuesto.repuesto))

        if taller_id:
            q_parts = q_parts.join(Inventario, Inventario.id == InventarioRepuesto.inventario_id).where(Inventario.taller_id == taller_id)
            q_crit = q_crit.join(Inventario, Inventario.id == InventarioRepuesto.inventario_id).where(Inventario.taller_id == taller_id)
            q_val = q_val.join(Inventario, Inventario.id == InventarioRepuesto.inventario_id).where(Inventario.taller_id == taller_id)

        total_parts = (await self.db.execute(q_parts)).scalar_one()
        critical_parts = (await self.db.execute(q_crit)).scalar_one()

        total_inventory_value = 0.0
        inv_result = await self.db.execute(q_val)
        for item in inv_result.scalars().all():
            total_inventory_value += item.cantidad * float(item.repuesto.precio)

        return {
            "total_requests": total_requests,
            "active_requests": active_requests,
            "completed_requests": completed_requests,
            "total_mechanics": total_mechanics,
            "available_mechanics": available_mechanics,
            "total_parts": total_parts,
            "critical_parts": critical_parts,
            "inventory_value": round(total_inventory_value, 2),
        }
