from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


# ── Enums ──

class ServiceType(str, Enum):
    TOWING = "towing"
    TIRE_CHANGE = "tire_change"
    BATTERY = "battery"
    LOCKOUT = "lockout"
    FUEL = "fuel"
    DIAGNOSTICS = "diagnostics"
    BRAKES = "brakes"
    OIL_CHANGE = "oil_change"
    TRANSMISSION = "transmission"
    GENERAL = "general"


class Status(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    CRITICO = "CRITICO"
    COMPLETADO = "COMPLETADO"
    RECHAZADO = "RECHAZADO"


class Priority(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


# ── Mapeo de íconos por tipo de servicio ──

SERVICE_ICONS: dict[str, str] = {
    "towing": "local_shipping",
    "tire_change": "tire_repair",
    "battery": "battery_charging_full",
    "lockout": "lock_open",
    "fuel": "local_gas_station",
    "diagnostics": "monitor_heart",
    "brakes": "auto_fix_high",
    "oil_change": "oil_barrel",
    "transmission": "settings",
    "general": "build",
}

SERVICE_LABELS: dict[str, str] = {
    "towing": "Grúa / Remolque",
    "tire_change": "Cambio de Neumático",
    "battery": "Servicio de Batería",
    "lockout": "Apertura de Vehículo",
    "fuel": "Suministro de Combustible",
    "diagnostics": "Diagnóstico",
    "brakes": "Reparación de Frenos",
    "oil_change": "Cambio de Aceite",
    "transmission": "Transmisión",
    "general": "Servicio General",
}


# ── Request schemas ──

class ServiceRequestCreate(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=100)
    vehicle_info: str = Field(..., min_length=2, max_length=200)
    service_type: ServiceType
    description: str = Field(default="", max_length=1000)
    location: str = Field(..., min_length=2, max_length=200)
    priority: Priority = Priority.MEDIA


class ServiceRequestUpdate(BaseModel):
    status: Status | None = None
    assigned_mechanic: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    description: str | None = Field(default=None, max_length=1000)
    priority: Priority | None = None


# ── Response schemas ──

class ServiceRequestResponse(BaseModel):
    id: int
    code: str
    client_name: str
    vehicle_info: str
    service_type: str
    service_type_label: str = ""
    service_icon: str = ""
    description: str
    location: str
    status: str
    priority: str
    assigned_mechanic: str | None
    progress: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    user_id: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj) -> "ServiceRequestResponse":
        data = {
            "id": obj.id,
            "code": obj.code,
            "client_name": obj.client_name,
            "vehicle_info": obj.vehicle_info,
            "service_type": obj.service_type,
            "service_type_label": SERVICE_LABELS.get(obj.service_type, obj.service_type),
            "service_icon": SERVICE_ICONS.get(obj.service_type, "build"),
            "description": obj.description,
            "location": obj.location,
            "status": obj.status,
            "priority": obj.priority,
            "assigned_mechanic": obj.assigned_mechanic,
            "progress": obj.progress,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "completed_at": obj.completed_at,
            "user_id": obj.user_id,
        }
        return cls(**data)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class ServiceRequestStats(BaseModel):
    total_queue: int
    avg_lead_time_hours: float
    critical_count: int
    completion_rate: float
