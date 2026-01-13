from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.llm.openai_client import OpenAIChatClient, OpenAIEmbeddingsClient
from app.services.settings_store import (
    get_llm_provider_settings_raw,
    resolve_llm_provider_effective_config,
)


@dataclass(frozen=True)
class EffectiveLlmProviderConfig:
    api_key: str | None
    base_url: str | None
    model: str
    embeddings_model: str
    timeout_s: float
    max_retries: int


def _settings_from_app(app: FastAPI) -> Settings:
    settings = getattr(app.state, "settings", None)
    if settings is None:
        raise RuntimeError("settings_not_initialized")
    return settings


async def resolve_effective_provider_config(
    *,
    session: AsyncSession,
    app: FastAPI,
) -> EffectiveLlmProviderConfig:
    settings = _settings_from_app(app)
    stored = await get_llm_provider_settings_raw(session=session)
    effective = resolve_llm_provider_effective_config(stored=stored, env_settings=settings)
    return EffectiveLlmProviderConfig(
        api_key=effective.get("api_key"),
        base_url=effective.get("base_url"),
        model=str(effective.get("model") or settings.openai_model),
        embeddings_model=str(effective.get("embeddings_model") or settings.openai_embeddings_model),
        timeout_s=float(effective.get("timeout_s") or settings.openai_timeout_s),
        max_retries=int(effective.get("max_retries") or settings.openai_max_retries),
    )


async def resolve_llm_client(
    *,
    session: AsyncSession,
    app: FastAPI,
) -> LLMClient | None:
    override = getattr(app.state, "llm_client", None)
    if override is not None:
        return override

    cfg = await resolve_effective_provider_config(session=session, app=app)
    if not cfg.api_key:
        return None
    return OpenAIChatClient(
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        model=cfg.model,
        timeout_s=cfg.timeout_s,
        max_retries=cfg.max_retries,
    )


async def resolve_embeddings_client(
    *,
    session: AsyncSession,
    app: FastAPI,
) -> EmbeddingsClient | None:
    override = getattr(app.state, "embeddings_client", None)
    if override is not None:
        return override

    cfg = await resolve_effective_provider_config(session=session, app=app)
    if not cfg.api_key:
        return None
    return OpenAIEmbeddingsClient(
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        model=cfg.embeddings_model,
        timeout_s=cfg.timeout_s,
        max_retries=cfg.max_retries,
    )


async def resolve_llm_and_embeddings(
    *,
    session: AsyncSession,
    app: FastAPI,
) -> tuple[LLMClient | None, EmbeddingsClient | None, dict[str, Any]]:
    override_llm = getattr(app.state, "llm_client", None)
    override_embeddings = getattr(app.state, "embeddings_client", None)
    if override_llm is not None and override_embeddings is not None:
        return (
            override_llm,
            override_embeddings,
            {"effective": {"api_key_present": True, "source": "override"}},
        )

    cfg = await resolve_effective_provider_config(session=session, app=app)

    llm: LLMClient | None = override_llm
    embeddings: EmbeddingsClient | None = override_embeddings

    if llm is None and cfg.api_key:
        llm = OpenAIChatClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            model=cfg.model,
            timeout_s=cfg.timeout_s,
            max_retries=cfg.max_retries,
        )

    if embeddings is None and cfg.api_key:
        embeddings = OpenAIEmbeddingsClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            model=cfg.embeddings_model,
            timeout_s=cfg.timeout_s,
            max_retries=cfg.max_retries,
        )

    meta = {
        "effective": {
            "base_url": cfg.base_url,
            "model": cfg.model,
            "embeddings_model": cfg.embeddings_model,
            "timeout_s": cfg.timeout_s,
            "max_retries": cfg.max_retries,
            "api_key_present": bool(cfg.api_key),
            "source": "db/env",
        }
    }
    return llm, embeddings, meta
