"""Enumeraciones del dominio Auxilio Mecánico."""

import enum


class EstadoSolicitud(str, enum.Enum):
    """Estados posibles de una solicitud de servicio."""

    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    RECHAZADA = "RECHAZADA"
    CRITICO = "CRITICO"


class MetodoPago(str, enum.Enum):
    """Métodos de pago aceptados."""

    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    MERCADOPAGO = "MERCADOPAGO"


class EstadoPago(str, enum.Enum):
    """Estados posibles de un pago."""

    PENDIENTE = "PENDIENTE"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"
    REEMBOLSADO = "REEMBOLSADO"
