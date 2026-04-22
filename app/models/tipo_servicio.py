"""Modelo TipoServicio — catálogo de tipos de servicio mecánico."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.solicitud_servicio import SolicitudServicio


class TipoServicio(Base):
    __tablename__ = "tipos_servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio_base: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # Relaciones
    solicitudes: Mapped[list["SolicitudServicio"]] = relationship(
        back_populates="tipo_servicio"
    )
