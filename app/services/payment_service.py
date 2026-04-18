import logging

import httpx

from app.core.config import get_settings
from app.schemas.payment import PaymentPreferenceRequest

logger = logging.getLogger(__name__)

MERCADOPAGO_API_URL = "https://api.mercadopago.com/checkout/preferences"


class PaymentService:
    """Crea preferencias de pago en MercadoPago."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_preference(
        self, payload: PaymentPreferenceRequest
    ) -> dict[str, str]:
        """Crea una preferencia y devuelve init_point + preference_id."""
        body = {
            "items": [
                {
                    "title": payload.description,
                    "quantity": 1,
                    "unit_price": payload.amount,
                    "currency_id": "BOB",
                }
            ],
            "external_reference": payload.request_id,
            "back_urls": {
                "success": self.settings.mercadopago_back_urls_success,
                "failure": self.settings.mercadopago_back_urls_failure,
                "pending": self.settings.mercadopago_back_urls_pending,
            },
            "auto_return": "approved",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MERCADOPAGO_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.settings.mercadopago_access_token}",
                },
                json=body,
            )
            response.raise_for_status()

        data = response.json()
        return {
            "init_point": data["init_point"],
            "preference_id": data["id"],
        }
