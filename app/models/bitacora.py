from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Bitacora(Base):
    __tablename__ = "bitacora"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    accion = Column(String(50), nullable=False)
    entidad = Column(String(100), nullable=False)
    entidad_id = Column(String(100), nullable=True)
    detalles = Column(JSON, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario")
