from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient


class OpenAIChatClient:
    def __init__(self, *, api_key: str, model: str, timeout_s: float) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_s)
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAIChatClient | None:
        if not settings.openai_api_key:
            return None
        return cls(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout_s=settings.openai_timeout_s,
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


class OpenAIEmbeddingsClient:
    def __init__(self, *, api_key: str, model: str, timeout_s: float) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_s)
        self._model = model

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAIEmbeddingsClient | None:
        if not settings.openai_api_key:
            return None
        return cls(
            api_key=settings.openai_api_key,
            model=settings.openai_embeddings_model,
            timeout_s=settings.openai_timeout_s,
        )

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in resp.data]


def as_llm_client(client: OpenAIChatClient | None) -> LLMClient | None:
    return client


def as_embeddings_client(client: OpenAIEmbeddingsClient | None) -> EmbeddingsClient | None:
    return client
