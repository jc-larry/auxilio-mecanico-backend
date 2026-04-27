from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, RequireRoles, get_user_taller_id
from app.core.permissions import RoleEnum
from app.models.usuario import Usuario
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
async def get_analytics(
    taller_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(RequireRoles([RoleEnum.ADMINISTRADOR, RoleEnum.PROPIETARIO])),
) -> dict:
    user_taller_id = get_user_taller_id(current_user)
    final_taller_id = user_taller_id if user_taller_id else taller_id
    service = AnalyticsService(db)
    return await service.get_dashboard_analytics(final_taller_id)
