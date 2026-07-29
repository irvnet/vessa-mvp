"""Shared startup: build the compiled Vessa agent + its store/checkpointer
(singletons). SQLite-backed — state survives a server restart."""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_memory_store():
    from app.persistence import build_sqlite_store

    return build_sqlite_store()


@lru_cache(maxsize=1)
def get_checkpointer():
    from app.persistence import build_sqlite_saver

    return build_sqlite_saver()


@lru_cache(maxsize=1)
def build_compiled_agent():
    """Eager agent — used by FastAPI lifespan (warm on startup)."""
    from app.agent import build_agent

    logger.info("Bootstrap: creating Vessa agent (SQLite-backed persistence)...")
    return build_agent(store=get_memory_store(), checkpointer=get_checkpointer())
