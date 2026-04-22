"""Modelo Cliente — usuario con rol de cliente."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.calificacion import Calificacion
    from app.models.solicitud_servicio import SolicitudServicio
    from app.models.usuario import Usuario
    from app.models.vehiculo import Vehiculo


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), unique=True, nullable=False
    )

    # Relaciones
    usuario: Mapped["Usuario"] = relationship(back_populates="cliente")
    vehiculos: Mapped[list["Vehiculo"]] = relationship(back_populates="cliente")
    solicitudes: Mapped[list["SolicitudServicio"]] = relationship(
        back_populates="cliente"
    )
    calificaciones: Mapped[list["Calificacion"]] = relationship(
        back_populates="cliente"
    )
