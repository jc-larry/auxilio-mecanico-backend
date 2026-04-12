from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

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


class Expertise(str, Enum):
    SENIOR = "SENIOR"
    INTERMEDIO = "INTERMEDIO"
    JUNIOR = "JUNIOR"


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

EXPERTISE_LABELS: dict[str, str] = {
    "SENIOR": "Senior",
    "INTERMEDIO": "Intermedio",
    "JUNIOR": "Junior",
}


# ── Request schemas ──

class MechanicCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(default="", max_length=20)
    specialty: Specialty = Specialty.GENERAL
    expertise: Expertise = Expertise.JUNIOR
    avatar_color: str = Field(default="#091426", max_length=10)


class MechanicUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    specialty: Specialty | None = None
    expertise: Expertise | None = None
    is_available: bool | None = None
    avatar_color: str | None = Field(default=None, max_length=10)


# ── Response schemas ──

class MechanicResponse(BaseModel):
    id: int
    employee_code: str
    full_name: str
    initials: str = ""
    phone: str
    specialty: str
    specialty_label: str = ""
    specialty_icon: str = ""
    expertise: str
    expertise_label: str = ""
    is_available: bool
    avatar_color: str
    created_at: datetime
    updated_at: datetime
    user_id: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj) -> "MechanicResponse":
        name = obj.full_name or ""
        parts = name.split()
        initials = "".join(p[0] for p in parts[:2]).upper() if parts else "?"

        return cls(
            id=obj.id,
            employee_code=obj.employee_code,
            full_name=obj.full_name,
            initials=initials,
            phone=obj.phone,
            specialty=obj.specialty,
            specialty_label=SPECIALTY_LABELS.get(obj.specialty, obj.specialty),
            specialty_icon=SPECIALTY_ICONS.get(obj.specialty, "build"),
            expertise=obj.expertise,
            expertise_label=EXPERTISE_LABELS.get(obj.expertise, obj.expertise),
            is_available=obj.is_available,
            avatar_color=obj.avatar_color,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            user_id=obj.user_id,
        )


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class MechanicStats(BaseModel):
    total: int
    available: int
    unavailable: int
    top_specialty: str
    top_specialty_count: int
