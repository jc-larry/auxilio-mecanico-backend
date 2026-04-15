from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.models.mechanic import Mechanic
from app.models.service_request import ServiceRequest
from app.schemas.inventory import SYSTEM_LABELS
from app.schemas.service_request import SERVICE_LABELS


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_dashboard_analytics(self) -> dict:
        """Aggregate analytics data from all modules."""
        return {
            "requests_by_day": await self._requests_by_day(),
            "requests_by_type": await self._requests_by_type(),
            "requests_by_status": await self._requests_by_status(),
            "mechanic_workload": await self._mechanic_workload(),
            "inventory_by_system": await self._inventory_by_system(),
            "summary": await self._summary(),
        }

    async def _requests_by_day(self) -> list[dict]:
        """Service requests per day for the last 7 days."""
        now = datetime.now(timezone.utc)
        days = []

        for i in range(6, -1, -1):
            target_date = now - timedelta(days=i)
            day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            result = await self.db.execute(
                select(func.count()).where(
                    ServiceRequest.created_at >= day_start,
                    ServiceRequest.created_at <= day_end,
                )
            )
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

    async def _requests_by_type(self) -> list[dict]:
        """Distribution of service requests by type."""
        result = await self.db.execute(select(ServiceRequest.service_type))
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

    async def _requests_by_status(self) -> list[dict]:
        """Count of requests per status."""
        statuses = ["PENDIENTE", "EN_PROGRESO", "CRITICO", "COMPLETADO", "RECHAZADO"]
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
            result = await self.db.execute(
                select(func.count()).where(ServiceRequest.status == s)
            )
            count = result.scalar_one()
            items.append({
                "status": s,
                "label": status_labels.get(s, s),
                "count": count,
                "color": status_colors.get(s, "#94a3b8"),
            })

        return items

    async def _mechanic_workload(self) -> list[dict]:
        """How many assigned requests per mechanic."""
        result = await self.db.execute(
            select(
                ServiceRequest.assigned_mechanic,
                func.count(ServiceRequest.id),
            )
            .where(ServiceRequest.assigned_mechanic.isnot(None))
            .group_by(ServiceRequest.assigned_mechanic)
        )
        rows = result.all()

        items = []
        for name, count in rows:
            parts = name.split()
            initials = "".join(p[0] for p in parts[:2]).upper() if parts else "?"
            items.append({
                "name": name,
                "initials": initials,
                "assigned_count": count,
            })

        # Sort by count descending
        items.sort(key=lambda x: x["assigned_count"], reverse=True)
        return items

    async def _inventory_by_system(self) -> list[dict]:
        """Inventory units grouped by system category."""
        result = await self.db.execute(
            select(
                InventoryItem.system_category,
                func.sum(InventoryItem.quantity),
                func.count(InventoryItem.id),
            )
            .group_by(InventoryItem.system_category)
        )
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

    async def _summary(self) -> dict:
        """High-level summary counters."""
        total_requests = (await self.db.execute(select(func.count(ServiceRequest.id)))).scalar_one()
        completed_requests = (await self.db.execute(
            select(func.count()).where(ServiceRequest.status == "COMPLETADO")
        )).scalar_one()
        active_requests = total_requests - completed_requests

        total_mechanics = (await self.db.execute(select(func.count(Mechanic.id)))).scalar_one()
        available_mechanics = (await self.db.execute(
            select(func.count()).where(Mechanic.is_available == True)  # noqa: E712
        )).scalar_one()

        total_parts = (await self.db.execute(select(func.count(InventoryItem.id)))).scalar_one()
        critical_parts = (await self.db.execute(
            select(func.count()).where(InventoryItem.is_critical == True)  # noqa: E712
        )).scalar_one()

        total_inventory_value = 0.0
        inv_result = await self.db.execute(select(InventoryItem))
        for item in inv_result.scalars().all():
            total_inventory_value += item.quantity * item.unit_price

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
