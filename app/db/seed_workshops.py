import asyncio
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.taller import Taller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_workshops():
    async with AsyncSessionLocal() as db:
        logger.info("Verificando talleres...")
        
        workshops = [
            {
                "nombre": "Taller Central Mecánica",
                "direccion": "Av. Bush #123, Santa Cruz",
                "latitud": -17.7833,
                "longitud": -63.1821,
                "telefono": "70012345",
                "estado": True
            },
            {
                "nombre": "Grúas y Servicios Bolivia",
                "direccion": "4to Anillo y Radial 26, Santa Cruz",
                "latitud": -17.7700,
                "longitud": -63.1700,
                "telefono": "71055566",
                "estado": True
            },
            {
                "nombre": "Auto Service Express",
                "direccion": "Calle 21 de Calacoto, La Paz",
                "latitud": -16.5400,
                "longitud": -68.0700,
                "telefono": "22778899",
                "estado": True
            },
            {
                "nombre": "Mecánica Sur",
                "direccion": "Av. Santos Dumont, Santa Cruz",
                "latitud": -17.8200,
                "longitud": -63.1900,
                "telefono": "33344455",
                "estado": True
            }
        ]
        
        for w_data in workshops:
            stmt = select(Taller).where(Taller.nombre == w_data["nombre"])
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                taller = Taller(**w_data)
                db.add(taller)
                logger.info(f"Creado taller: {w_data['nombre']}")
        
        await db.commit()
        logger.info("Talleres verificados/creados.")

if __name__ == "__main__":
    asyncio.run(seed_workshops())
