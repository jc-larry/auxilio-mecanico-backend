from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class BitacoraUsuarioSimple(BaseModel):
    """Schema ligero del usuario para la bitácora — sin roles ni permisos."""
    id: int
    email: str

    full_name: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, obj) -> "BitacoraUsuarioSimple":
        if not obj:
            return None
        return cls(
            id=getattr(obj, "id", 0),
            email=getattr(obj, "email", "n/a"),
            full_name=getattr(obj, "nombre", "Usuario Desconocido"),
        )


class BitacoraResponse(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    accion: str
    entidad: str
    entidad_id: Optional[str] = None
    detalles: Optional[Dict[str, Any]] = None
    fecha_hora: datetime
    usuario: Optional[BitacoraUsuarioSimple] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, obj) -> "BitacoraResponse":
        usuario = None
        if hasattr(obj, "usuario") and obj.usuario:
            usuario = BitacoraUsuarioSimple.from_model(obj.usuario)

        return cls(
            id=obj.id,
            usuario_id=obj.usuario_id,
            accion=obj.accion,
            entidad=obj.entidad,
            entidad_id=obj.entidad_id,
            detalles=obj.detalles,
            fecha_hora=obj.fecha_hora,
            usuario=usuario,
        )



