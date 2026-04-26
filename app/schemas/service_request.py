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
    cliente_id: int
    vehiculo_id: int
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
        # Extraer nombres de relaciones si están cargadas
        client_name = "Cliente Desconocido"
        if hasattr(obj, "cliente") and obj.cliente and obj.cliente.usuario:
            client_name = obj.cliente.usuario.nombre

        vehicle_info = "Vehículo Desconocido"
        if hasattr(obj, "vehiculo") and obj.vehiculo:
            vehicle_info = f"{obj.vehiculo.marca} {obj.vehiculo.modelo} ({obj.vehiculo.placa})"

        assigned_mechanic = None
        if hasattr(obj, "mecanico") and obj.mecanico and obj.mecanico.usuario:
            assigned_mechanic = obj.mecanico.usuario.nombre

        # Mapeo de estados (legacy usa COMPLETADO, nuevo usa COMPLETADA)
        status_map = {
            "COMPLETADA": "COMPLETADO",
            "CANCELADA": "RECHAZADO",
            "RECHAZADA": "RECHAZADO"
        }
        status = status_map.get(obj.estado.value if hasattr(obj.estado, "value") else obj.estado, 
                                obj.estado.value if hasattr(obj.estado, "value") else obj.estado)

        # Determinar el tipo de servicio (legacy usa string, nuevo usa ID/objeto)
        # Por ahora asumimos que el nuevo modelo tiene el código en tipo_servicio.nombre o similar
        service_type = "general"
        if hasattr(obj, "tipo_servicio") and obj.tipo_servicio:
            # Buscar el valor inverso en SERVICE_LABELS o usar el nombre directo
            service_type = obj.tipo_servicio.nombre

        data = {
            "id": obj.id,
            "code": obj.codigo,
            "client_name": client_name,
            "vehicle_info": vehicle_info,
            "service_type": service_type,
            "service_type_label": SERVICE_LABELS.get(service_type, service_type),
            "service_icon": SERVICE_ICONS.get(service_type, "build"),
            "description": obj.descripcion_problema,
            "location": obj.ubicacion,
            "status": status,
            "priority": obj.prioridad,
            "assigned_mechanic": assigned_mechanic,
            "progress": obj.progreso,
            "created_at": obj.fecha_creacion,
            "updated_at": obj.fecha_creacion, # Simplificación
            "completed_at": obj.fecha_fin,
            "user_id": obj.usuario_id,
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
