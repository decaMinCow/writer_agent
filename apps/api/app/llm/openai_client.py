from __future__ import annotations

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient


class OpenAIChatClient:
    def __init__(self, *, api_key: str, model: str, timeout_s: float, base_url: str | None = None) -> None:
        kwargs: dict[str, object] = {"api_key": api_key, "timeout": timeout_s}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAIChatClient | None:
        if not settings.openai_api_key:
            return None
        return cls(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout_s=settings.openai_timeout_s,
            base_url=settings.resolved_openai_base_url(),
        )

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or ""

    async def stream_complete(self, *, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            stream=True,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content


class OpenAIEmbeddingsClient:
    def __init__(self, *, api_key: str, model: str, timeout_s: float, base_url: str | None = None) -> None:
        kwargs: dict[str, object] = {"api_key": api_key, "timeout": timeout_s}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAIEmbeddingsClient | None:
        if not settings.openai_api_key:
            return None
        return cls(
            api_key=settings.openai_api_key,
            model=settings.openai_embeddings_model,
            timeout_s=settings.openai_timeout_s,
            base_url=settings.resolved_openai_base_url(),
        )

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in resp.data]


def as_llm_client(client: OpenAIChatClient | None) -> LLMClient | None:
    return client


def as_embeddings_client(client: OpenAIEmbeddingsClient | None) -> EmbeddingsClient | None:
    return client
