from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="dev", validation_alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/writer_agent",
        validation_alias="DATABASE_URL",
    )
    cors_allow_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ALLOW_ORIGINS",
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    openai_embeddings_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDINGS_MODEL"
    )
    openai_timeout_s: float = Field(default=60, validation_alias="OPENAI_TIMEOUT_S")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


def load_settings() -> Settings:
    return Settings()
