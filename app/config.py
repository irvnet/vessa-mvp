import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"  # used only if/when semantic memory search is added

# Real persistence for the live app (app/persistence.py) — scripts/tests keep
# using the in-memory defaults in agent.py, so this only affects bootstrap.py.
SQLITE_DB_PATH = ROOT / "data" / "vessa.db"

# Cached eval-run summaries, read by the /proof page — written by each eval
# script's __main__ block, read instantly (no LLM cost) on page load.
EVAL_RESULTS_PATH = ROOT / "data" / "eval_results.json"


def load_env() -> None:
    """Load .env — supports both `export KEY=val` (notebook) and `KEY=val` (systemd)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ")
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, val.strip().strip('"').strip("'"))
