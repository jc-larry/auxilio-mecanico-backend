from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import RequirePermissions
from app.core.permissions import PermissionEnum
from app.models.usuario import Usuario
from app.schemas.bitacora import BitacoraResponse
from app.schemas.common import PaginatedResponse
from app.services.bitacora_service import BitacoraService

router = APIRouter(prefix="/bitacora", tags=["Bitácora"])

@router.get("", response_model=PaginatedResponse[BitacoraResponse])
async def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.BITACORA_VER]))
):
    service = BitacoraService(db)
    result = await service.list_logs(page=page, per_page=per_page)

    return PaginatedResponse(
        items=[BitacoraResponse.from_model(item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        pages=result["pages"],
    )
