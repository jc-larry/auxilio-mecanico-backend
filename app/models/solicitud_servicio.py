"""Modelos SolicitudServicio, HistorialEstadoSolicitud y SolicitudRepuesto."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EstadoSolicitud

if TYPE_CHECKING:
    from app.models.calificacion import Calificacion
    from app.models.cliente import Cliente
    from app.models.mecanico import Mecanico
    from app.models.pago import Pago
    from app.models.repuesto import Repuesto
    from app.models.taller import Taller
    from app.models.tipo_servicio import TipoServicio
    from app.models.vehiculo import Vehiculo


class SolicitudServicio(Base):
    __tablename__ = "solicitudes_servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id"), nullable=False
    )
    taller_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("talleres.id"), nullable=True
    )
    mecanico_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("mecanicos.id"), nullable=True
    )
    tipo_servicio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tipos_servicio.id"), nullable=False
    )
    vehiculo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehiculos.id"), nullable=False
    )
    estado: Mapped[EstadoSolicitud] = mapped_column(
        Enum(EstadoSolicitud, name="estado_solicitud", native_enum=True),
        nullable=False,
        default=EstadoSolicitud.PENDIENTE,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    fecha_asignacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_inicio: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_fin: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    descripcion_problema: Mapped[str] = mapped_column(Text, nullable=False, default="")
    
    # Campos para retrocompatibilidad con dashboard legacy
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    prioridad: Mapped[str] = mapped_column(String(10), nullable=False, default="media")
    ubicacion: Mapped[str] = mapped_column(String(200), nullable=False)
    progreso: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Attachments
    url_imagen: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url_audio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Relaciones ───────────────────────────────────────────────────
    cliente: Mapped["Cliente"] = relationship(back_populates="solicitudes")
    taller: Mapped["Taller | None"] = relationship(back_populates="solicitudes")
    mecanico: Mapped["Mecanico | None"] = relationship(back_populates="solicitudes")
    tipo_servicio: Mapped["TipoServicio"] = relationship(back_populates="solicitudes")
    vehiculo: Mapped["Vehiculo"] = relationship(back_populates="solicitudes")

    historial_estados: Mapped[list["HistorialEstadoSolicitud"]] = relationship(
        back_populates="solicitud", cascade="all, delete-orphan"
    )
    pago: Mapped["Pago | None"] = relationship(
        back_populates="solicitud", uselist=False
    )
    solicitud_repuestos: Mapped[list["SolicitudRepuesto"]] = relationship(
        back_populates="solicitud", cascade="all, delete-orphan"
    )
    calificaciones: Mapped[list["Calificacion"]] = relationship(
        back_populates="solicitud"
    )


class HistorialEstadoSolicitud(Base):
    __tablename__ = "historial_estado_solicitud"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    solicitud_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("solicitudes_servicio.id"), nullable=False
    )
    estado: Mapped[EstadoSolicitud] = mapped_column(
        Enum(EstadoSolicitud, name="estado_solicitud", native_enum=True, create_type=False),
        nullable=False,
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    solicitud: Mapped["SolicitudServicio"] = relationship(
        back_populates="historial_estados"
    )


class SolicitudRepuesto(Base):
    __tablename__ = "solicitud_repuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    solicitud_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("solicitudes_servicio.id"), nullable=False
    )
    repuesto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repuestos.id", ondelete="CASCADE"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )

    # Relaciones
    solicitud: Mapped["SolicitudServicio"] = relationship(
        back_populates="solicitud_repuestos"
    )
    repuesto: Mapped["Repuesto"] = relationship(back_populates="solicitud_repuestos")
