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
    allowed_origins: list[str] = ["http://localhost:4200"]

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # MercadoPago
    mercadopago_access_token: str = ""
    mercadopago_back_urls_success: str = "https://rapidrescue.app/payment/success"
    mercadopago_back_urls_failure: str = "https://rapidrescue.app/payment/failure"
    mercadopago_back_urls_pending: str = "https://rapidrescue.app/payment/pending"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
