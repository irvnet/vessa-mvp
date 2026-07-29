"""SQLite-backed persistence for the live app — conversations, memory, reminders,
and events survive a server restart. Scripts/tests keep using the in-memory
defaults in agent.py (fast, isolated, no file to clean up); only the running app
(bootstrap.py) opts into this."""

import sqlite3

from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.sqlite import SqliteStore

from app.config import EMBEDDING_MODEL, SQLITE_DB_PATH


def _connect() -> sqlite3.Connection:
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH), check_same_thread=False)
    # WAL mode — the two connections (saver + store) both write to this file;
    # the default rollback-journal locking doesn't handle that gracefully.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def build_sqlite_saver() -> SqliteSaver:
    """Its own connection — not shared with the store, to avoid two independent
    consumers interleaving transactions on one connection object."""
    conn = _connect()
    saver = SqliteSaver(conn)
    saver.setup()
    conn.commit()  # setup() leaves an open transaction (an uncommitted INSERT);
    # left open, it holds a write lock that blocks the store's own setup.
    return saver


def build_sqlite_store() -> SqliteStore:
    conn = _connect()
    store = SqliteStore(
        conn,
        index={"embed": OpenAIEmbeddings(model=EMBEDDING_MODEL), "dims": 1536},
    )
    store.setup()
    conn.commit()  # same reason — store_migrations INSERT is left uncommitted
    return store
