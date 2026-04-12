import math
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_request import ServiceRequest
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestStats,
    ServiceRequestUpdate,
)


class ServiceRequestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _generate_code(self) -> str:
        """Auto-generate sequential code like SR-0001, SR-0002..."""
        result = await self.db.execute(
            select(func.count(ServiceRequest.id))
        )
        count = result.scalar_one()
        return f"SR-{count + 1:04d}"

    async def create(self, data: ServiceRequestCreate, user_id: int) -> ServiceRequest:
        code = await self._generate_code()
        sr = ServiceRequest(
            code=code,
            client_name=data.client_name,
            vehicle_info=data.vehicle_info,
            service_type=data.service_type.value,
            description=data.description,
            location=data.location,
            priority=data.priority.value,
            status="PENDIENTE",
            progress=0,
            user_id=user_id,
        )
        self.db.add(sr)
        await self.db.commit()
        await self.db.refresh(sr)
        return sr

    async def get_by_id(self, request_id: int) -> ServiceRequest | None:
        result = await self.db.execute(
            select(ServiceRequest).where(ServiceRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        status_filter: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[ServiceRequest], int]:
        """Return (items, total_count) with optional status filter and pagination."""
        query = select(ServiceRequest)

        if status_filter:
            query = query.where(ServiceRequest.status == status_filter)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated results (newest first)
        query = query.order_by(ServiceRequest.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, request_id: int, data: ServiceRequestUpdate) -> ServiceRequest | None:
        sr = await self.get_by_id(request_id)
        if not sr:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                # Convert enum values to strings
                if hasattr(value, "value"):
                    value = value.value
                setattr(sr, field, value)

        # Auto-set completed_at when status changes to COMPLETADO
        if data.status and data.status.value == "COMPLETADO":
            sr.completed_at = datetime.now(timezone.utc)
            sr.progress = 100

        # Auto-clear completed_at if status changes away from COMPLETADO
        if data.status and data.status.value != "COMPLETADO" and sr.completed_at:
            sr.completed_at = None

        sr.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(sr)
        return sr

    async def delete(self, request_id: int) -> bool:
        sr = await self.get_by_id(request_id)
        if not sr:
            return False
        await self.db.delete(sr)
        await self.db.commit()
        return True

    async def get_stats(self) -> ServiceRequestStats:
        """Calculate dynamic KPIs."""
        # Total active (not COMPLETADO)
        active_query = select(func.count()).where(
            ServiceRequest.status != "COMPLETADO"
        )
        active_result = await self.db.execute(active_query)
        total_queue = active_result.scalar_one()

        # Critical count
        critical_query = select(func.count()).where(
            ServiceRequest.status == "CRITICO"
        )
        critical_result = await self.db.execute(critical_query)
        critical_count = critical_result.scalar_one()

        # Completion rate
        total_query = select(func.count(ServiceRequest.id))
        total_result = await self.db.execute(total_query)
        total_all = total_result.scalar_one()

        completed_query = select(func.count()).where(
            ServiceRequest.status == "COMPLETADO"
        )
        completed_result = await self.db.execute(completed_query)
        completed_count = completed_result.scalar_one()

        completion_rate = (completed_count / total_all * 100) if total_all > 0 else 0.0

        # Average lead time (hours) for completed requests
        completed_items_query = select(ServiceRequest).where(
            ServiceRequest.status == "COMPLETADO",
            ServiceRequest.completed_at.isnot(None),
        )
        completed_items_result = await self.db.execute(completed_items_query)
        completed_items = list(completed_items_result.scalars().all())

        avg_lead_time = 0.0
        if completed_items:
            total_hours = sum(
                (item.completed_at - item.created_at).total_seconds() / 3600
                for item in completed_items
            )
            avg_lead_time = round(total_hours / len(completed_items), 1)

        return ServiceRequestStats(
            total_queue=total_queue,
            avg_lead_time_hours=avg_lead_time,
            critical_count=critical_count,
            completion_rate=round(completion_rate, 1),
        )
