"""Application settings loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base application configuration."""

    secret_key: str = Field(
        "e1d73525f5cf6009603ce3d52c5640d4069b65f877d8b1fdfe2bd0387a4473dc",
        alias="SECRET_KEY",
    )
    session_secret: str = Field("secret-key-1234", alias="SESSION_SECRET")
    celery_broker_url: str = Field("redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        "redis://localhost:6379/0",
        alias="CELERY_RESULT_BACKEND",
    )
    cors_origins: List[str] = Field(default_factory=lambda: ["https://example.com"], alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value):  # type: ignore[override]
        if isinstance(value, str):
            if not value:
                return []
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


settings = get_settings()