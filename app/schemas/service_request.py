from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ──

# Eliminado: class ServiceType(str, Enum) ya que usaremos el modelo TipoServicio de la DB

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

# SERVICE_LABELS eliminado, se usará el nombre del TipoServicio

# ── Request schemas ──

class ServiceRequestCreate(BaseModel):
    cliente_id: int
    vehiculo_id: int
    tipo_servicio_id: int
    description: str = Field(default="", max_length=1000)
    location: str = Field(..., min_length=2, max_length=200)
    priority: Priority = Priority.MEDIA
    url_imagen: str | None = None
    url_audio: str | None = None


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
    url_imagen: str | None = None
    url_audio: str | None = None

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

        # Mapeo de estados
        status_map = {
            "COMPLETADA": "COMPLETADO",
            "CANCELADA": "RECHAZADO",
            "RECHAZADA": "RECHAZADO"
        }
        status = status_map.get(obj.estado.value if hasattr(obj.estado, "value") else obj.estado, 
                                obj.estado.value if hasattr(obj.estado, "value") else obj.estado)

        # Determinar el tipo de servicio (legacy usa string, nuevo usa ID/objeto)
        service_type = "general"
        service_type_label = "Servicio General"
        if hasattr(obj, "tipo_servicio") and obj.tipo_servicio:
            service_type = obj.tipo_servicio.nombre.lower().replace(" ", "_")
            service_type_label = obj.tipo_servicio.nombre

        # Mapa de iconos según el tipo de servicio
        SERVICE_ICONS = {
            "grúa_/_remolque": "local_shipping",
            "cambio_de_neumático": "tire_repair",
            "servicio_de_batería": "battery_charging_full",
            "apertura_de_vehículo": "lock_open",
            "suministro_de_combustible": "local_gas_station",
            "diagnóstico": "biotech",
            "reparación_de_frenos": "car_repair",
            "cambio_de_aceite": "oil_barrel",
            "transmisión": "rebase_edit",
            "servicio_general": "build"
        }

        data = {
            "id": obj.id,
            "code": obj.codigo,
            "client_name": client_name,
            "vehicle_info": vehicle_info,
            "service_type": service_type,
            "service_type_label": service_type_label,
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
            "url_imagen": obj.url_imagen,
            "url_audio": obj.url_audio,
        }
        return cls(**data)





class ServiceRequestStats(BaseModel):
    total_queue: int
    avg_lead_time_hours: float
    critical_count: int
    completion_rate: float
