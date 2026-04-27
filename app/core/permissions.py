from enum import Enum


class RoleEnum(str, Enum):
    ADMINISTRADOR = "Administrador"
    PROPIETARIO = "Propietario"
    MECANICO = "Mecánico"
    CLIENTE = "Cliente"


class PermissionEnum(str, Enum):
    # Usuarios
    USUARIOS_CREAR = "usuarios.crear"
    USUARIOS_VER = "usuarios.ver"
    USUARIOS_EDITAR = "usuarios.editar"
    USUARIOS_ELIMINAR = "usuarios.eliminar"
    USUARIOS_ASIGNAR_ROL = "usuarios.asignar_rol"

    # ROLES
    ROLES_VER = "roles.ver"
    ROLES_CREAR = "roles.crear"
    ROLES_EDITAR = "roles.editar"
    ROLES_ELIMINAR = "roles.eliminar"

    # Clientes
    CLIENTES_CREAR = "clientes.crear"
    CLIENTES_VER = "clientes.ver"
    CLIENTES_EDITAR = "clientes.editar"
    CLIENTES_ELIMINAR = "clientes.eliminar"

    # VEHICULOS
    VEHICULOS_CREAR = "vehiculos.crear"
    VEHICULOS_VER = "vehiculos.ver"
    VEHICULOS_EDITAR = "vehiculos.editar"
    VEHICULOS_ELIMINAR = "vehiculos.eliminar"

    # Servicios
    SERVICIOS_VER = "servicios.ver"
    SERVICIOS_CREAR = "servicios.crear"
    SERVICIOS_EDITAR = "servicios.editar"
    SERVICIOS_ELIMINAR = "servicios.eliminar"

    # Solicitudes / Citas
    SOLICITUDES_CREAR = "solicitudes.crear"
    SOLICITUDES_VER = "solicitudes.ver"
    SOLICITUDES_ACEPTAR = "solicitudes.aceptar"
    SOLICITUDES_RECHAZAR = "solicitudes.rechazar"
    SOLICITUDES_ASIGNAR_MECANICO = "solicitudes.asignar_mecanico"
    SOLICITUDES_CAMBIAR_ESTADO = "solicitudes.cambiar_estado"

    # Inventario / Repuestos
    INVENTARIO_VER = "inventario.ver"
    INVENTARIO_AGREGAR = "inventario.agregar"
    INVENTARIO_EDITAR = "inventario.editar"
    INVENTARIO_ELIMINAR = "inventario.eliminar"
    INVENTARIO_AJUSTAR_STOCK = "inventario.ajustar_stock"

    # Talleres
    TALLERES_VER = "talleres.ver"
    TALLERES_CREAR = "talleres.crear"
    TALLERES_EDITAR = "talleres.editar"
    TALLERES_ELIMINAR = "talleres.eliminar"
    TALLERES_ANALITICAS = "talleres.analiticas"

    # FACTURAS
    FACTURAS_CREAR = "facturas.crear"
    FACTURAS_VER = "facturas.ver"
    FACTURAS_ANULAR = "facturas.anular"

    # PAGOS
    PAGOS_REGISTRAR = "pagos.registrar"
    PAGOS_VER = "pagos.ver"

    # BITÁCORA
    BITACORA_VER = "bitacora.ver"
