"""Modelo Calificacion — calificación emitida por un cliente sobre un servicio."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.solicitud_servicio import SolicitudServicio
    from app.models.taller import Taller


class Calificacion(Base):
    __tablename__ = "calificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    solicitud_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("solicitudes_servicio.id"), nullable=False
    )
    cliente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id"), nullable=False
    )
    taller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("talleres.id"), nullable=False
    )
    puntuacion: Mapped[int] = mapped_column(Integer, nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones
    solicitud: Mapped["SolicitudServicio"] = relationship(
        back_populates="calificaciones"
    )
    cliente: Mapped["Cliente"] = relationship(back_populates="calificaciones")
    taller: Mapped["Taller"] = relationship(back_populates="calificaciones")
