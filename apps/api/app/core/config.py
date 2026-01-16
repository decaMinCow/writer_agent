from __future__ import annotations

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="dev", validation_alias="APP_ENV")
    auto_migrate: bool = Field(default=False, validation_alias="AUTO_MIGRATE")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/writer_agent",
        validation_alias="DATABASE_URL",
    )
    static_dir: str | None = Field(default=None, validation_alias="STATIC_DIR")
    cors_allow_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ALLOW_ORIGINS",
    )
    cors_allow_origin_regex: str | None = Field(
        default=r"^https?://(localhost|127[.]0[.]0[.]1)(:[0-9]+)?$",
        validation_alias="CORS_ALLOW_ORIGIN_REGEX",
    )

    openai_base_url: str | None = Field(
        default=None,
        validation_alias="OPENAI_BASE_URL",
    )
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_embeddings_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDINGS_MODEL"
    )
    openai_timeout_s: float = Field(default=60, validation_alias="OPENAI_TIMEOUT_S")
    openai_max_retries: int = Field(default=2, validation_alias="OPENAI_MAX_RETRIES")
    license_public_key: str | None = Field(default=None, validation_alias="LICENSE_PUBLIC_KEY")
    license_required: bool = Field(default=False, validation_alias="LICENSE_REQUIRED")
    license_machine_salt: str = Field(default="writer_agent2", validation_alias="LICENSE_MACHINE_SALT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    def cors_origin_regex(self) -> str | None:
        value = self.cors_allow_origin_regex
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def resolved_openai_base_url(self) -> str | None:
        value = self.openai_base_url
        if value is None:
            value = os.getenv("OPENAI_BASE_URL")
        if not value:
            return None
        return str(value).strip() or None


def load_settings() -> Settings:
    return Settings()
