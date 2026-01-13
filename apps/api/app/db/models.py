from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SAEnum

from app.db.base import Base

EMBEDDING_DIM = 1536


class ArtifactKind(str, enum.Enum):
    novel_chapter = "novel_chapter"
    script_scene = "script_scene"


class ArtifactVersionSource(str, enum.Enum):
    user = "user"
    agent = "agent"


class WorkflowKind(str, enum.Enum):
    novel = "novel"
    script = "script"
    novel_to_script = "novel_to_script"


class RunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    paused = "paused"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class BriefMessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    snapshots: Mapped[list[BriefSnapshot]] = relationship(
        back_populates="brief", cascade="all, delete-orphan"
    )
    messages: Mapped[list[BriefMessage]] = relationship(
        back_populates="brief", cascade="all, delete-orphan"
    )


class BriefSnapshot(Base):
    __tablename__ = "brief_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("briefs.id"), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    brief: Mapped[Brief] = relationship(back_populates="snapshots")


class BriefMessage(Base):
    __tablename__ = "brief_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("briefs.id"), nullable=False)
    role: Mapped[BriefMessageRole] = mapped_column(
        SAEnum(BriefMessageRole, name="brief_message_role"), nullable=False
    )
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    brief: Mapped[Brief] = relationship(back_populates="messages")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[ArtifactKind] = mapped_column(
        SAEnum(ArtifactKind, name="artifact_kind"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    versions: Mapped[list[ArtifactVersion]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan"
    )


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[WorkflowKind] = mapped_column(
        SAEnum(WorkflowKind, name="workflow_kind"), nullable=False
    )
    status: Mapped[RunStatus] = mapped_column(SAEnum(RunStatus, name="run_status"), nullable=False)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    steps: Mapped[list[WorkflowStepRun]] = relationship(
        back_populates="workflow_run", cascade="all, delete-orphan"
    )


class WorkflowStepRun(Base):
    __tablename__ = "workflow_step_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[RunStatus] = mapped_column(SAEnum(RunStatus, name="step_status"), nullable=False)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    workflow_run: Mapped[WorkflowRun] = relationship(back_populates="steps")


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifacts.id"), nullable=False)
    source: Mapped[ArtifactVersionSource] = mapped_column(
        SAEnum(ArtifactVersionSource, name="artifact_version_source"), nullable=False
    )
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    workflow_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflow_runs.id"), nullable=True
    )
    brief_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    artifact: Mapped[Artifact] = relationship(back_populates="versions")


class MemoryChunk(Base):
    __tablename__ = "memory_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    artifact_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KgEntity(Base):
    __tablename__ = "kg_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KgRelation(Base):
    __tablename__ = "kg_relations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    subject_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("kg_entities.id"), nullable=False
    )
    predicate: Mapped[str] = mapped_column(String(64), nullable=False)
    object_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kg_entities.id"), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class KgEvent(Base):
    __tablename__ = "kg_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    event_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    time_hint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    artifact_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=True
    )
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LintIssue(Base):
    __tablename__ = "lint_issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=True
    )
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PropagationEvent(Base):
    __tablename__ = "propagation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    base_artifact_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=False
    )
    edited_artifact_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=False
    )
    fact_changes: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ArtifactImpact(Base):
    __tablename__ = "artifact_impacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    propagation_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("propagation_events.id"), nullable=False
    )
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifacts.id"), nullable=False)
    artifact_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    repaired_artifact_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=True
    )
    repaired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OpenThread(Base):
    __tablename__ = "open_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OpenThreadRef(Base):
    __tablename__ = "open_thread_refs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("open_threads.id"), nullable=False)
    artifact_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_versions.id"), nullable=False
    )
    ref_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SnapshotGlossaryEntry(Base):
    __tablename__ = "snapshot_glossary_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brief_snapshots.id"), nullable=False
    )
    term: Mapped[str] = mapped_column(String(255), nullable=False)
    replacement: Mapped[str] = mapped_column(String(255), nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
