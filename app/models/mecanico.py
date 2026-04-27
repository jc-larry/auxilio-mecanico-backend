"""Modelo Mecanico — mecánico asignado a un taller."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.solicitud_servicio import SolicitudServicio
    from app.models.taller import Taller
    from app.models.usuario import Usuario


class Mecanico(Base):
    __tablename__ = "mecanicos"

    # ── Campos del diagrama ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), unique=True, nullable=False
    )
    taller_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("talleres.id"), nullable=True
    )
    especialidad: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general"
    )
    disponible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relaciones ───────────────────────────────────────────────────
    usuario: Mapped["Usuario"] = relationship(back_populates="mecanico")
    taller: Mapped["Taller | None"] = relationship(back_populates="mecanicos")
    solicitudes: Mapped[list["SolicitudServicio"]] = relationship(
        back_populates="mecanico"
    )
