import logging
from typing import BinaryIO

import cloudinary
import cloudinary.uploader

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class UploadService:
    """Sube archivos a Cloudinary y devuelve la URL pública."""

    def __init__(self) -> None:
        settings = get_settings()
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    async def upload_file(
        self, file: BinaryIO, filename: str, content_type: str
    ) -> dict[str, str]:
        """Sube un archivo y devuelve url + tipo detectado."""
        media_type = self._detect_type(content_type)

        # Cloudinary resource_type: image, video, raw
        resource_type = "video" if media_type in ("video", "audio") else "image"

        result = cloudinary.uploader.upload(
            file,
            folder="rapidrescue/attachments",
            resource_type=resource_type,
            public_id=filename.rsplit(".", 1)[0] if "." in filename else filename,
        )

        return {
            "url": result["secure_url"],
            "type": media_type,
            "public_id": result["public_id"],
        }

    @staticmethod
    def _detect_type(content_type: str) -> str:
        if content_type.startswith("image/"):
            return "image"
        if content_type.startswith("video/"):
            return "video"
        if content_type.startswith("audio/"):
            return "audio"
        return "other"
