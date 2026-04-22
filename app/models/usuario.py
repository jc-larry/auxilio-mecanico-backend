"""Modelo Usuario — mapea la entidad Usuario del diagrama de clases."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.mecanico import Mecanico
    from app.models.rol import Rol


class Usuario(Base):
    __tablename__ = "usuarios"

    # ── Campos del diagrama ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Campos legacy (auth existente, no están en el diagrama) ──────
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relaciones ───────────────────────────────────────────────────
    roles: Mapped[list["Rol"]] = relationship(
        secondary="usuario_roles", back_populates="usuarios"
    )
    cliente: Mapped["Cliente | None"] = relationship(
        back_populates="usuario", uselist=False
    )
    mecanico: Mapped["Mecanico | None"] = relationship(
        back_populates="usuario", uselist=False
    )
