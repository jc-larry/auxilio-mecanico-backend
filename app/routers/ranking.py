import logging

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError

from app.core.config import get_settings
from app.core.dependencies import get_current_user, RequireRoles
from app.core.permissions import RoleEnum
from app.models.usuario import Usuario
from app.schemas.ranking import RankingRequest, RankingResponse
from app.services.ranking_service import RankingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ranking", tags=["Ranking"])


@router.post("", response_model=RankingResponse)
async def rank_workshops(
    payload: RankingRequest,
    _: Usuario = Depends(RequireRoles([RoleEnum.CLIENTE, RoleEnum.ADMINISTRADOR])),
):
    """Genera un ranking de talleres usando Claude como LLM.

    Recibe los datos de la solicitud y la lista de talleres candidatos,
    los envía a Claude para su análisis y devuelve los talleres ordenados
    por puntaje de compatibilidad.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está configurado. Configura ANTHROPIC_API_KEY en el .env",
        )

    try:
        service = RankingService()
        rankings = await service.rank_workshops(payload)
        return RankingResponse(rankings=rankings)
    except HTTPStatusError as exc:
        logger.error("Error al llamar a Anthropic: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al conectar con el servicio de IA",
        )
    except Exception as exc:
        logger.error("Error inesperado en ranking: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el ranking",
        )
