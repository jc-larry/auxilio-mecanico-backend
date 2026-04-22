"""Modelo Repuesto — catálogo de repuestos/piezas."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.inventario import InventarioRepuesto
    from app.models.solicitud_servicio import SolicitudRepuesto


class Repuesto(Base):
    __tablename__ = "repuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    sku: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    system_category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")

    # Relaciones
    solicitud_repuestos: Mapped[list["SolicitudRepuesto"]] = relationship(
        back_populates="repuesto"
    )
    inventario_repuestos: Mapped[list["InventarioRepuesto"]] = relationship(
        back_populates="repuesto"
    )
