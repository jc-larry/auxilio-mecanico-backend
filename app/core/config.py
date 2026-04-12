from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Auth System API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Security
    secret_key: str = "your-super-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "sqlite+aiosqlite:///./auth.db"

    # CORS
    allowed_origins: list[str] = ["http://localhost:4200"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
