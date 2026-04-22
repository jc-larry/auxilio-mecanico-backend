"""Modelos Rol, Permiso y tablas asociativas usuario_roles / roles_permisos."""

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario

# ── Tablas asociativas (M2M) ─────────────────────────────────────────

usuario_roles = Table(
    "usuario_roles",
    Base.metadata,
    Column("usuario_id", Integer, ForeignKey("usuarios.id"), primary_key=True),
    Column("rol_id", Integer, ForeignKey("roles.id"), primary_key=True),
)

roles_permisos = Table(
    "roles_permisos",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permiso_id", Integer, ForeignKey("permisos.id"), primary_key=True),
)


# ── Modelos ──────────────────────────────────────────────────────────


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relaciones
    usuarios: Mapped[list["Usuario"]] = relationship(
        secondary=usuario_roles, back_populates="roles"
    )
    permisos: Mapped[list["Permiso"]] = relationship(
        secondary=roles_permisos, back_populates="roles"
    )


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relaciones
    roles: Mapped[list["Rol"]] = relationship(
        secondary=roles_permisos, back_populates="permisos"
    )
