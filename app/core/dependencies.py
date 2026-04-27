from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.usuario import Usuario
from app.services.user_service import UserService

bearer_scheme = HTTPBearer()

def get_user_taller_id(user: Usuario) -> int | None:
    is_admin = any(r.nombre == "Administrador" for r in getattr(user, "roles", []))
    if is_admin:
        return None

    if getattr(user, "mecanico", None):
        return user.mecanico.taller_id
    
    if getattr(user, "propietario", None):
        if user.propietario.talleres:
            return user.propietario.talleres[0].id
            
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    token = credentials.credentials
    payload = decode_token(token)

    user_id: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")

    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = UserService(db)
    user = await service.get_by_id(int(user_id))

    if not user or not user.estado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_with_permissions(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Obtiene el usuario actual con sus roles y permisos cargados."""
    token = credentials.credentials
    payload = decode_token(token)

    user_id: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")

    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = UserService(db)
    user = await service.get_by_id_with_permissions(int(user_id))

    if not user or not user.estado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


class RequirePermissions:
    """
    Dependencia para verificar si el usuario tiene los permisos requeridos.
    Uso: @router.get("/...", dependencies=[Depends(RequirePermissions([PermissionEnum.USUARIOS_VER]))])
    """

    def __init__(self, required_permissions: list[str]) -> None:
        self.required_permissions = [
            p.value if hasattr(p, "value") else str(p) for p in required_permissions
        ]

    async def __call__(self, user: Usuario = Depends(get_current_user_with_permissions)) -> Usuario:
        # Extraer permisos del usuario
        user_permissions = set()
        for rol in user.roles:
            for permiso in rol.permisos:
                user_permissions.add(permiso.nombre)
        
        # Verificar si tiene todos los permisos requeridos
        for req_perm in self.required_permissions:
            if req_perm not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required: {req_perm}",
                )
        
        return user


class RequireRoles:
    """
    Dependencia para verificar si el usuario tiene al menos uno de los roles requeridos.
    Uso: @router.get("/...", dependencies=[Depends(RequireRoles([RoleEnum.ADMINISTRADOR]))])
    """

    def __init__(self, required_roles: list[str]) -> None:
        self.required_roles = [
            r.value if hasattr(r, "value") else str(r) for r in required_roles
        ]

    async def __call__(self, user: Usuario = Depends(get_current_user_with_permissions)) -> Usuario:
        user_roles = {rol.nombre for rol in user.roles}
        
        if not any(role in user_roles for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough roles to access this resource",
            )
            
        return user
