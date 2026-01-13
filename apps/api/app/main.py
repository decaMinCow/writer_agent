from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routers.analysis import router as analysis_router
from app.api.routers.artifacts import router as artifacts_router
from app.api.routers.brief_snapshots import router as brief_snapshots_router
from app.api.routers.briefs import router as briefs_router
from app.api.routers.exports import router as exports_router
from app.api.routers.open_threads import router as open_threads_router
from app.api.routers.propagation import router as propagation_router
from app.api.routers.settings import router as settings_router
from app.api.routers.workflows import router as workflows_router
from app.core.config import Settings, load_settings
from app.llm.client import LLMClient
from app.llm.embeddings_client import EmbeddingsClient
from app.services.workflow_events import WorkflowEventHub


def create_app(
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    embeddings_client: EmbeddingsClient | None = None,
) -> FastAPI:
    settings = settings or load_settings()

    app = FastAPI(title="writer_agent2 API")
    app.state.settings = settings
    # Optional test/dev overrides. When unset, LLM clients are resolved per request from DB/env settings.
    app.state.llm_client = llm_client
    app.state.embeddings_client = embeddings_client
    app.state.workflow_event_hub = WorkflowEventHub()
    app.state.workflow_autorun_tasks = {}
    app.state.workflow_autorun_stop_flags = {}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_origin_regex=settings.cors_origin_regex(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(settings_router)
    app.include_router(briefs_router)
    app.include_router(brief_snapshots_router)
    app.include_router(artifacts_router)
    app.include_router(workflows_router)
    app.include_router(analysis_router)
    app.include_router(propagation_router)
    app.include_router(open_threads_router)
    app.include_router(exports_router)

    @app.on_event("startup")
    async def _startup() -> None:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        app.state.engine = engine
        app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        engine = getattr(app.state, "engine", None)
        if engine:
            await engine.dispose()

    return app


app = create_app()
