from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ──

class Specialty(str, Enum):
    DIESEL = "diesel"
    ELECTRICO = "electrico"
    HIDRAULICA = "hidraulica"
    TRANSMISION = "transmision"
    DIAGNOSTICO = "diagnostico"
    GENERAL = "general"
    GRUA = "grua"
    NEUMATICOS = "neumaticos"
    FRENOS = "frenos"
    CARROCERIA = "carroceria"



# ── Mapeos de UI ──

SPECIALTY_LABELS: dict[str, str] = {
    "diesel": "Motor Diésel",
    "electrico": "Sistemas Eléctricos",
    "hidraulica": "Hidráulica",
    "transmision": "Transmisión",
    "diagnostico": "Diagnóstico",
    "general": "Mecánica General",
    "grua": "Grúa / Remolque",
    "neumaticos": "Neumáticos",
    "frenos": "Frenos",
    "carroceria": "Carrocería",
}

SPECIALTY_ICONS: dict[str, str] = {
    "diesel": "settings",
    "electrico": "bolt",
    "hidraulica": "precision_manufacturing",
    "transmision": "directions_car",
    "diagnostico": "monitor_heart",
    "general": "build",
    "grua": "local_shipping",
    "neumaticos": "tire_repair",
    "frenos": "auto_fix_high",
    "carroceria": "directions_car",
}




# ── Request schemas ──

class MechanicCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    specialty: Specialty = Specialty.GENERAL
    workshop_id: int | None = None


class MechanicUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    specialty: Specialty | None = None
    is_available: bool | None = None
    workshop_id: int | None = None


# ── Response schemas ──

class MechanicResponse(BaseModel):
    id: int
    full_name: str
    initials: str = ""
    specialty: str
    specialty_label: str = ""
    specialty_icon: str = ""
    is_available: bool
    created_at: datetime
    updated_at: datetime
    user_id: int
    workshop_id: int | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj) -> "MechanicResponse":
        # full_name comes from the related usuario if available, otherwise fallback
        name = ""
        if hasattr(obj, "usuario") and obj.usuario:
            name = obj.usuario.nombre
        parts = name.split() if name else []
        initials = "".join(p[0] for p in parts[:2]).upper() if parts else "?"

        return cls(
            id=obj.id,
            full_name=name,
            initials=initials,
            specialty=obj.especialidad,
            specialty_label=SPECIALTY_LABELS.get(obj.especialidad, obj.especialidad),
            specialty_icon=SPECIALTY_ICONS.get(obj.especialidad, "build"),
            is_available=obj.disponible,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            user_id=obj.usuario_id,
            workshop_id=obj.taller_id,
        )





class MechanicStats(BaseModel):
    total: int
    available: int
    unavailable: int
    top_specialty: str
    top_specialty_count: int
