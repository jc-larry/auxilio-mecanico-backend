from typing import Any, Dict, Optional, List
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload

from app.models.bitacora import Bitacora

class BitacoraService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        usuario_id: Optional[int],
        accion: str,
        entidad: str,
        entidad_id: Optional[str] = None,
        detalles: Optional[Dict[str, Any]] = None
    ) -> Bitacora:
        """
        Registra una acción en la bitácora.
        """
        bitacora = Bitacora(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
            detalles=detalles
        )
        self.db.add(bitacora)
        # Importante: No hacemos commit aquí para que el commit se maneje en la transacción superior.
        return bitacora

    async def list_logs(self, page: int = 1, per_page: int = 20):
        """
        Lista los registros de la bitácora con paginación.
        """
        # Calcular total
        total_stmt = select(func.count()).select_from(Bitacora)
        total_res = await self.db.execute(total_stmt)
        total = total_res.scalar_one()

        pages = math.ceil(total / per_page) if total > 0 else 1
        if page > pages:
            page = pages
            
        offset = (page - 1) * per_page

        # Obtener items
        stmt = (
            select(Bitacora)
            .options(joinedload(Bitacora.usuario))
            .order_by(desc(Bitacora.fecha_hora))
            .offset(offset)
            .limit(per_page)
        )
        res = await self.db.execute(stmt)
        items = res.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }
