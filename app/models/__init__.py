"""Módulo de modelos — importa todas las entidades para descubrimiento por Alembic/Base."""

# Enums
from app.models.enums import EstadoPago, EstadoSolicitud, MetodoPago  # noqa: F401

# Modelos principales (diagrama de clases)
from app.models.usuario import Usuario  # noqa: F401
from app.models.rol import Permiso, Rol, roles_permisos, usuario_roles  # noqa: F401
from app.models.cliente import Cliente  # noqa: F401
from app.models.vehiculo import Vehiculo  # noqa: F401
from app.models.mecanico import Mecanico  # noqa: F401
from app.models.taller import Taller  # noqa: F401
from app.models.tipo_servicio import TipoServicio  # noqa: F401
from app.models.solicitud_servicio import (  # noqa: F401
    HistorialEstadoSolicitud,
    SolicitudRepuesto,
    SolicitudServicio,
)
from app.models.calificacion import Calificacion  # noqa: F401
from app.models.pago import Factura, Pago  # noqa: F401
from app.models.repuesto import Repuesto  # noqa: F401
from app.models.inventario import Inventario, InventarioRepuesto  # noqa: F401

# Aliases — retrocompatibilidad con servicios existentes
User = Usuario
Mechanic = Mecanico
