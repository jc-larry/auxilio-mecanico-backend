import logging

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.payment import PaymentPreferenceRequest, PaymentPreferenceResponse
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-preference", response_model=PaymentPreferenceResponse)
async def create_preference(
    payload: PaymentPreferenceRequest,
    _: User = Depends(get_current_user),
):
    """Crea una preferencia de pago en MercadoPago.

    Devuelve la URL de checkout (init_point) que el cliente abre en un WebView.
    """
    settings = get_settings()
    if not settings.mercadopago_access_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de pagos no está configurado. Configura MERCADOPAGO_ACCESS_TOKEN en el .env",
        )

    try:
        service = PaymentService()
        result = await service.create_preference(payload)
        return PaymentPreferenceResponse(**result)
    except HTTPStatusError as exc:
        logger.error("Error al crear preferencia en MercadoPago: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al conectar con el servicio de pagos",
        )
    except Exception as exc:
        logger.error("Error inesperado en pagos: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear la preferencia de pago",
        )
