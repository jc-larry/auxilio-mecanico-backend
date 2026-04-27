from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── Enums ──

class SystemCategory(str, Enum):
    HIDRAULICA = "hidraulica"
    ELECTRICO = "electrico"
    MOTOR = "motor"
    COMBUSTION = "combustion"
    LUBRICACION = "lubricacion"
    FRENOS = "frenos"
    NEUMATICOS = "neumaticos"
    TRANSMISION = "transmision"
    CARROCERIA = "carroceria"
    GENERAL = "general"


# ── Mapeos ──

SYSTEM_LABELS: dict[str, str] = {
    "hidraulica": "Sistema Hidráulico",
    "electrico": "Sistema Eléctrico",
    "motor": "Motor",
    "combustion": "Combustión Interna",
    "lubricacion": "Lubricación",
    "frenos": "Sistema de Frenos",
    "neumaticos": "Neumáticos",
    "transmision": "Transmisión",
    "carroceria": "Carrocería",
    "general": "General",
}

SYSTEM_ICONS: dict[str, str] = {
    "hidraulica": "settings_input_component",
    "electrico": "bolt",
    "motor": "settings",
    "combustion": "local_fire_department",
    "lubricacion": "oil_barrel",
    "frenos": "auto_fix_high",
    "neumaticos": "tire_repair",
    "transmision": "precision_manufacturing",
    "carroceria": "directions_car",
    "general": "build",
}


# ── Request schemas ──

class InventoryItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    sku: str = Field(..., min_length=2, max_length=30)
    system_category: SystemCategory = SystemCategory.GENERAL
    quantity: int = Field(default=0, ge=0)
    min_stock: int = Field(default=5, ge=0)
    unit_price: float = Field(default=0.0, ge=0)


class InventoryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    system_category: SystemCategory | None = None
    quantity: int | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    unit_price: float | None = Field(default=None, ge=0)


class RestockRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Cantidad a agregar al stock")


# ── Response schemas ──

class InventoryItemResponse(BaseModel):
    id: int
    sku: str
    name: str
    system_category: str
    system_label: str = ""
    icon: str = ""
    quantity: int
    min_stock: int
    unit_price: float
    is_critical: bool
    created_at: datetime
    updated_at: datetime
    user_id: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, repuesto: "Repuesto", inv_item: "InventarioRepuesto | None" = None) -> "InventoryItemResponse":
        # repuesto is a Repuesto instance.
        # inv_item is an optional InventarioRepuesto instance.
        
        quantity = inv_item.cantidad if inv_item else 0
        min_stock = inv_item.min_stock if inv_item else 5
        is_critical = quantity <= min_stock

        return cls(
            id=repuesto.id,  # Use Repuesto ID as the primary identifier
            sku=repuesto.sku,
            name=repuesto.nombre,
            system_category=repuesto.system_category,
            system_label=SYSTEM_LABELS.get(repuesto.system_category, repuesto.system_category),
            icon=SYSTEM_ICONS.get(repuesto.system_category, "build"),
            quantity=quantity,
            min_stock=min_stock,
            unit_price=float(repuesto.precio),
            is_critical=is_critical,
            created_at=datetime.now(),  # Placeholder
            updated_at=datetime.now(),  # Placeholder
            user_id=0,  # Placeholder
        )





class InventoryStats(BaseModel):
    total_items: int
    total_units: int
    critical_count: int
    total_value: float
