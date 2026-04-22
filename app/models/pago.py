"""Modelos Pago y Factura."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EstadoPago, MetodoPago

if TYPE_CHECKING:
    from app.models.solicitud_servicio import SolicitudServicio


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    solicitud_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("solicitudes_servicio.id"), unique=True, nullable=False
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    metodo_pago: Mapped[MetodoPago] = mapped_column(
        Enum(MetodoPago, name="metodo_pago", native_enum=True),
        nullable=False,
    )
    estado: Mapped[EstadoPago] = mapped_column(
        Enum(EstadoPago, name="estado_pago", native_enum=True),
        nullable=False,
        default=EstadoPago.PENDIENTE,
    )
    fecha_pago: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relaciones
    solicitud: Mapped["SolicitudServicio"] = relationship(back_populates="pago")
    factura: Mapped["Factura | None"] = relationship(
        back_populates="pago", uselist=False
    )


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pago_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pagos.id"), unique=True, nullable=False
    )
    numero_factura: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    impuesto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relaciones
    pago: Mapped["Pago"] = relationship(back_populates="factura")
