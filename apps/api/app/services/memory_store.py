from __future__ import annotations

import math
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MemoryChunk
from app.llm.embeddings_client import EmbeddingsClient


def _cosine_distance(a: object, b: list[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    try:
        iterator = iter(a)  # type: ignore[arg-type]
    except TypeError:
        return 1.0

    for ax, bx in zip(iterator, b, strict=False):
        a_f = float(ax)
        b_f = float(bx)
        dot += a_f * b_f
        norm_a += a_f * a_f
        norm_b += b_f * b_f
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 1.0
    return 1.0 - (dot / (math.sqrt(norm_a) * math.sqrt(norm_b)))


def chunk_text(text: str, *, max_chars: int = 900, overlap_chars: int = 100) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if not current:
            return
        chunks.append("\n\n".join(current).strip())
        current = []
        current_len = 0

    for paragraph in paragraphs:
        if current_len + len(paragraph) + 2 > max_chars and current:
            flush()
        current.append(paragraph)
        current_len += len(paragraph) + 2

    flush()

    if overlap_chars > 0 and len(chunks) > 1:
        overlapped: list[str] = []
        prev_tail = ""
        for chunk in chunks:
            if prev_tail:
                overlapped.append((prev_tail + "\n\n" + chunk).strip())
            else:
                overlapped.append(chunk)
            prev_tail = chunk[-overlap_chars:] if len(chunk) > overlap_chars else chunk
        return overlapped

    return chunks


async def index_artifact_version(
    *,
    session: AsyncSession,
    embeddings: EmbeddingsClient,
    brief_snapshot_id: uuid.UUID,
    artifact_version_id: uuid.UUID,
    content_text: str,
    meta: dict[str, Any] | None = None,
) -> int:
    chunks = chunk_text(content_text)
    if not chunks:
        return 0

    vectors = await embeddings.embed(texts=chunks)
    if len(vectors) != len(chunks):
        raise RuntimeError("embeddings_count_mismatch")

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
        session.add(
            MemoryChunk(
                brief_snapshot_id=brief_snapshot_id,
                artifact_version_id=artifact_version_id,
                chunk_index=idx,
                content_text=chunk,
                embedding=vector,
                meta=meta or {},
            )
        )

    await session.commit()
    return len(chunks)


async def retrieve_evidence(
    *,
    session: AsyncSession,
    embeddings: EmbeddingsClient,
    brief_snapshot_id: uuid.UUID,
    query: str,
    limit: int = 8,
) -> list[MemoryChunk]:
    limit = max(1, min(limit, 20))
    query_vec = (await embeddings.embed(texts=[query]))[0]

    bind = session.get_bind()
    dialect_name = getattr(getattr(bind, "dialect", None), "name", None)

    if dialect_name == "postgresql":
        stmt = (
            select(MemoryChunk)
            .where(MemoryChunk.brief_snapshot_id == brief_snapshot_id)
            .order_by(MemoryChunk.embedding.cosine_distance(query_vec))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    result = await session.execute(
        select(MemoryChunk).where(MemoryChunk.brief_snapshot_id == brief_snapshot_id)
    )
    rows = list(result.scalars().all())
    rows.sort(key=lambda row: _cosine_distance(row.embedding, query_vec))
    return rows[:limit]
