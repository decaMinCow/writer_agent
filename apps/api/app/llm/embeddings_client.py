from __future__ import annotations

from typing import Protocol


class EmbeddingsClient(Protocol):
    async def embed(self, *, texts: list[str]) -> list[list[float]]: ...

