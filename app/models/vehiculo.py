"""Modelo Vehiculo — vehículo propiedad de un cliente."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.solicitud_servicio import SolicitudServicio


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id"), nullable=False
    )
    marca: Mapped[str] = mapped_column(String(50), nullable=False)
    modelo: Mapped[str] = mapped_column(String(50), nullable=False)
    placa: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(30), nullable=False)

    # Relaciones
    cliente: Mapped["Cliente"] = relationship(back_populates="vehiculos")
    solicitudes: Mapped[list["SolicitudServicio"]] = relationship(
        back_populates="vehiculo"
    )
