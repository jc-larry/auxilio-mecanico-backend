from pydantic import BaseModel, Field


class WorkshopInput(BaseModel):
    """Un taller candidato enviado por el cliente."""

    id: str
    name: str
    address: str
    distance_km: float = 0.0
    rating: float = 0.0
    review_count: int = 0
    specialties: list[str] = []
    is_open: bool = True
    phone: str | None = None


class RankingRequestData(BaseModel):
    """Datos de la solicitud de servicio para el ranking."""

    description: str
    urgency: str = "normal"
    problem_type: str = "other"
    vehicle_brand: str = ""
    vehicle_model: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


class RankingRequest(BaseModel):
    """Payload completo para POST /ranking."""

    request_data: RankingRequestData
    workshops: list[WorkshopInput] = Field(..., min_length=1)


class WorkshopRankingItem(BaseModel):
    """Un taller rankeado con su puntaje y justificación."""

    id: str
    name: str
    address: str
    distance_km: float
    rating: float
    review_count: int
    match_score: int = Field(ge=0, le=100)
    ai_reasoning: str
    specialties: list[str] = []
    is_open: bool = True
    phone: str | None = None


class RankingResponse(BaseModel):
    """Respuesta con la lista de talleres rankeados."""

    rankings: list[WorkshopRankingItem]
