from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KgEntity, KgEvent, KgRelation


class PostgresKgStore:
    async def clear_snapshot(self, *, session: AsyncSession, brief_snapshot_id: uuid.UUID) -> None:
        await session.execute(
            delete(KgRelation).where(KgRelation.brief_snapshot_id == brief_snapshot_id)
        )
        await session.execute(delete(KgEvent).where(KgEvent.brief_snapshot_id == brief_snapshot_id))
        await session.execute(delete(KgEntity).where(KgEntity.brief_snapshot_id == brief_snapshot_id))
        await session.commit()

    async def upsert_entity(
        self,
        *,
        session: AsyncSession,
        brief_snapshot_id: uuid.UUID,
        name: str,
        entity_type: str,
        meta: dict[str, Any] | None = None,
    ) -> KgEntity:
        name = (name or "").strip()
        entity_type = (entity_type or "unknown").strip() or "unknown"
        if not name:
            raise ValueError("kg_entity_name_required")

        result = await session.execute(
            select(KgEntity).where(
                KgEntity.brief_snapshot_id == brief_snapshot_id,
                KgEntity.name == name,
                KgEntity.entity_type == entity_type,
            )
        )
        existing = result.scalars().first()
        if existing:
            if meta:
                existing.meta = dict(existing.meta or {}) | dict(meta)
                await session.flush()
            return existing

        entity = KgEntity(
            brief_snapshot_id=brief_snapshot_id,
            name=name,
            entity_type=entity_type,
            meta=meta or {},
        )
        session.add(entity)
        await session.flush()
        return entity

    async def add_relation(
        self,
        *,
        session: AsyncSession,
        brief_snapshot_id: uuid.UUID,
        subject_entity_id: uuid.UUID,
        predicate: str,
        object_entity_id: uuid.UUID,
        meta: dict[str, Any] | None = None,
    ) -> KgRelation:
        predicate = (predicate or "").strip()
        if not predicate:
            raise ValueError("kg_relation_predicate_required")

        relation = KgRelation(
            brief_snapshot_id=brief_snapshot_id,
            subject_entity_id=subject_entity_id,
            predicate=predicate,
            object_entity_id=object_entity_id,
            meta=meta or {},
        )
        session.add(relation)
        await session.flush()
        return relation

    async def add_event(
        self,
        *,
        session: AsyncSession,
        brief_snapshot_id: uuid.UUID,
        summary: str,
        artifact_version_id: uuid.UUID | None = None,
        event_key: str | None = None,
        time_hint: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> KgEvent:
        summary = (summary or "").strip()
        if not summary:
            raise ValueError("kg_event_summary_required")

        event = KgEvent(
            brief_snapshot_id=brief_snapshot_id,
            event_key=(event_key or "").strip() or None,
            summary=summary,
            time_hint=(time_hint or "").strip() or None,
            artifact_version_id=artifact_version_id,
            meta=meta or {},
        )
        session.add(event)
        await session.flush()
        return event
