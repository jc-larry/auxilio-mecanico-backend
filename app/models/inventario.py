"""Modelos Inventario e InventarioRepuesto — inventario por taller."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.repuesto import Repuesto
    from app.models.taller import Taller


class Inventario(Base):
    __tablename__ = "inventarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    taller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("talleres.id"), nullable=False
    )

    # Relaciones
    taller: Mapped["Taller"] = relationship(back_populates="inventarios")
    inventario_repuestos: Mapped[list["InventarioRepuesto"]] = relationship(
        back_populates="inventario", cascade="all, delete-orphan"
    )


class InventarioRepuesto(Base):
    __tablename__ = "inventario_repuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inventario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventarios.id"), nullable=False
    )
    repuesto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repuestos.id"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Relaciones
    inventario: Mapped["Inventario"] = relationship(
        back_populates="inventario_repuestos"
    )
    repuesto: Mapped["Repuesto"] = relationship(
        back_populates="inventario_repuestos"
    )
