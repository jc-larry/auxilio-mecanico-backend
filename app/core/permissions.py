from enum import Enum


class RoleEnum(str, Enum):
    ADMINISTRADOR = "Administrador"
    SUPERVISOR = "Supervisor"
    MECANICO = "Mecánico"
    CLIENTE = "Cliente"


class PermissionEnum(str, Enum):
    # Usuarios
    USUARIOS_CREAR = "usuarios.crear"
    USUARIOS_VER = "usuarios.ver"
    USUARIOS_EDITAR = "usuarios.editar"
    USUARIOS_ELIMINAR = "usuarios.eliminar"
    USUARIOS_ASIGNAR_ROL = "usuarios.asignar_rol"

    # Clientes & Vehículos
    CLIENTES_CREAR = "clientes.crear"
    CLIENTES_VER = "clientes.ver"
    CLIENTES_EDITAR = "clientes.editar"
    VEHICULOS_REGISTRAR = "vehiculos.registrar"
    VEHICULOS_VER = "vehiculos.ver"
    VEHICULOS_EDITAR = "vehiculos.editar"

    # Órdenes de Trabajo
    ORDENES_CREAR = "ordenes.crear"
    ORDENES_VER = "ordenes.ver"
    ORDENES_EDITAR = "ordenes.editar"
    ORDENES_ELIMINAR = "ordenes.eliminar"
    ORDENES_ASIGNAR_MECANICO = "ordenes.asignar_mecanico"
    ORDENES_CAMBIAR_ESTADO = "ordenes.cambiar_estado"
    ORDENES_APROBAR = "ordenes.aprobar"
    ORDENES_CERRAR = "ordenes.cerrar"

    # Solicitudes / Citas
    SOLICITUDES_CREAR = "solicitudes.crear"
    SOLICITUDES_VER = "solicitudes.ver"
    SOLICITUDES_ACEPTAR = "solicitudes.aceptar"
    SOLICITUDES_RECHAZAR = "solicitudes.rechazar"
    SOLICITUDES_REPROGRAMAR = "solicitudes.reprogramar"

    # Inventario / Repuestos
    INVENTARIO_VER = "inventario.ver"
    INVENTARIO_AGREGAR = "inventario.agregar"
    INVENTARIO_EDITAR = "inventario.editar"
    INVENTARIO_ELIMINAR = "inventario.eliminar"
    INVENTARIO_AJUSTAR_STOCK = "inventario.ajustar_stock"
