from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, RequireRoles
from app.core.permissions import RoleEnum
from app.models.usuario import Usuario
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
async def get_analytics(
    taller_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR, RoleEnum.PROPIETARIO])),
) -> dict:
    service = AnalyticsService(db)
    return await service.get_dashboard_analytics(taller_id)
