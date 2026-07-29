"""Cache for eval-run results, read by the /proof page. Read-merge-write —
three independent scripts each update only their own key, so running one
suite alone must never blank out another suite's last-cached result."""

import json
from datetime import datetime

from app.config import EVAL_RESULTS_PATH


def load_eval_summaries() -> dict:
    if not EVAL_RESULTS_PATH.exists():
        return {}
    return json.loads(EVAL_RESULTS_PATH.read_text())


def save_eval_summary(suite: str, summary: dict) -> None:
    data = load_eval_summaries()
    data[suite] = {**summary, "ran_at": datetime.now().isoformat()}
    EVAL_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_RESULTS_PATH.write_text(json.dumps(data, indent=2))
