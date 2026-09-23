"""Typed application configuration.

TODO:
- Load all values from the root .env file with pydantic-settings.
- Validate database, Nebius, upload, CORS, logging, and scheduler settings.
- Never hard-code or log secrets.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root: D:\FAM_DEMO
BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    APP_NAME: str = "Family Context Agent"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    DATABASE_URL: str

    FAMILY_TIMEZONE: str = "Asia/Kolkata"
    DEMO_FAMILY_NAME: str = "Nair Family"

    NEBIUS_API_KEY: str = ""
    NEBIUS_BASE_URL: str = "https://api.studio.nebius.ai/v1/"
    NVIDIA_MODEL_NAME: str = ""

    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_UPLOAD_TYPES: str = "application/pdf,image/jpeg,image/png"

    SCHEDULER_ENABLED: bool = True
    DEADLINE_CHECK_INTERVAL_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()