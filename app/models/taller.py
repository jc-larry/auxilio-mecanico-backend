"""Modelo Taller — taller mecánico con ubicación geográfica."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.calificacion import Calificacion
    from app.models.inventario import Inventario
    from app.models.mecanico import Mecanico
    from app.models.solicitud_servicio import SolicitudServicio


class Taller(Base):
    __tablename__ = "talleres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    mecanicos: Mapped[list["Mecanico"]] = relationship(back_populates="taller")
    solicitudes: Mapped[list["SolicitudServicio"]] = relationship(
        back_populates="taller"
    )
    inventarios: Mapped[list["Inventario"]] = relationship(back_populates="taller")
    calificaciones: Mapped[list["Calificacion"]] = relationship(
        back_populates="taller"
    )
