import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import RequirePermissions
from app.core.permissions import PermissionEnum
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.client import ClientResponse
from app.schemas.common import PaginatedResponse
from app.schemas.vehiculo import VehiculoResponse

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/{client_id}/vehicles", response_model=list[VehiculoResponse])
async def list_client_vehicles(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.VEHICULOS_VER])),
):
    result = await db.execute(select(Vehiculo).where(Vehiculo.cliente_id == client_id))
    return result.scalars().all()

@router.get("", response_model=PaginatedResponse[ClientResponse])
async def list_clients(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(RequirePermissions([PermissionEnum.CLIENTES_VER])),
):
    try:
        offset = (page - 1) * per_page
        
        # Base query
        query = select(Cliente).options(selectinload(Cliente.usuario))
        
        # Get total count
        total = await db.scalar(select(func.count(Cliente.id))) or 0
        
        # Get items
        result = await db.execute(query.offset(offset).limit(per_page))
        items = result.scalars().all()
        
        pages = math.ceil(total / per_page) if total > 0 else 1
        
        response_items = []
        for c in items:
            if c.usuario:
                response_items.append(
                    ClientResponse(
                        id=c.id,
                        usuario_id=c.usuario_id,
                        nombre=c.usuario.nombre,
                        email=c.usuario.email
                    )
                )
        
        return PaginatedResponse(
            items=response_items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al listar clientes: {str(e)}")
