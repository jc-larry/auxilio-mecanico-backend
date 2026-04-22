import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("")
async def upload_file(
    file: UploadFile,
    _: Usuario = Depends(get_current_user),
):
    """Sube un archivo (imagen, video, audio) a Cloudinary.

    Devuelve la URL pública del archivo subido y su tipo detectado.
    """
    settings = get_settings()
    if not settings.cloudinary_cloud_name:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de almacenamiento no está configurado. Configura las variables CLOUDINARY_* en el .env",
        )

    if file.size and file.size > 50 * 1024 * 1024:  # 50 MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el tamaño máximo de 50 MB",
        )

    try:
        service = UploadService()
        # Generar un nombre único para evitar colisiones
        unique_name = f"{uuid.uuid4().hex}_{file.filename or 'file'}"
        content_type = file.content_type or "application/octet-stream"

        result = await service.upload_file(file.file, unique_name, content_type)

        return {
            "url": result["url"],
            "type": result["type"],
            "public_id": result["public_id"],
        }
    except Exception as exc:
        logger.error("Error al subir archivo: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir el archivo",
        )
