"""Modelo Propietario — dueño de uno o más talleres."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.taller import Taller
    from app.models.usuario import Usuario


class Propietario(Base):
    __tablename__ = "propietarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), unique=True, nullable=False
    )

    # Relaciones
    usuario: Mapped["Usuario"] = relationship(back_populates="propietario")
    talleres: Mapped[list["Taller"]] = relationship(back_populates="propietario")
