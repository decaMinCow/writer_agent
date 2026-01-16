from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url


def _ensure_sqlite_directory(database_url: str) -> None:
    try:
        url = make_url(database_url)
    except Exception:
        return
    if url.get_backend_name() != "sqlite":
        return
    db_path = url.database
    if not db_path or db_path == ":memory:":
        return
    Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _upgrade_head_sync(database_url: str) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    alembic_ini = base_dir / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", database_url)

    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        _ensure_sqlite_directory(database_url)
        command.upgrade(config, "head")
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev


async def upgrade_head(*, database_url: str) -> None:
    await asyncio.to_thread(_upgrade_head_sync, database_url)
