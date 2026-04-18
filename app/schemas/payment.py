from pydantic import BaseModel, Field


class PaymentPreferenceRequest(BaseModel):
    """Payload para crear una preferencia de pago en MercadoPago."""

    request_id: str
    amount: float = Field(..., gt=0)
    description: str = "Servicio mecánico RapidRescue"


class PaymentPreferenceResponse(BaseModel):
    """Respuesta con la URL de checkout de MercadoPago."""

    init_point: str
    preference_id: str
