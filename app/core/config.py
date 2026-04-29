import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Auxilio Mecánico API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Security
    secret_key: str = "38944e15077c4258af3576ebf66a702638944e15077c4258af3576ebf66a7026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/auxilio_mecanico_db"

    # CORS
    allowed_origins: list[str] = ["*"]  # Permitir todos para desarrollo local

    # Google Gemini
    google_api_key: Optional[str] = None
    google_model: Optional[str] = None

    # Cloudinary
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None

    # MercadoPago
    mercadopago_access_token: Optional[str] = None
    mercadopago_back_urls_success: str = "https://rapidrescue.app/payment/success"
    mercadopago_back_urls_failure: str = "https://rapidrescue.app/payment/failure"
    mercadopago_back_urls_pending: str = "https://rapidrescue.app/payment/pending"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
