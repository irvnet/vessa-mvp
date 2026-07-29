"""Memory-quality eval — Vessa's differentiator is "it remembers you," but
nothing previously checked whether store.search() actually retrieves the
*right* past episode for a query, only that retrieval runs without erroring.
Tests retrieval directly (the same store.search() call companion_prompt makes
in app/agent.py), not the full agent/chat loop — cheaper, embeddings only.

Run: uv run python scripts/eval_memory.py
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.agent import build_memory_store, episode_namespace
from app.eval_persistence import save_eval_summary

CARE_TEAM_ID = "eval-memory-team"


@dataclass
class MemoryCase:
    id: str
    note: str
    query: str


CASES = [
    MemoryCase(
        "biscuit-eating",
        "Rose mentioned her cat Biscuit hasn't been eating much the past two days",
        "How has Biscuit been eating lately?",
    ),
    MemoryCase(
        "lighthouse-puzzle",
        "Rose started a new 1000-piece jigsaw puzzle of a lighthouse this week",
        "Tell me about the puzzle I'm working on",
    ),
    MemoryCase(
        "knee-soreness",
        "Rose mentioned her knee has been sore since Tuesday",
        "Have I said anything about knee pain?",
    ),
    MemoryCase(
        "mark-visit",
        "Rose's son Mark is visiting next weekend for her birthday",
        "When is Mark coming to visit?",
    ),
]

SEARCH_LIMIT = 5  # matches the real limit= used at runtime in app/agent.py's companion_prompt


def seed_episodes(store) -> None:
    base = datetime.now(timezone.utc)
    for i, case in enumerate(CASES):
        # Stagger keys slightly so ordering is deterministic if ever inspected.
        key = (base + timedelta(seconds=i)).isoformat()
        store.put(
            episode_namespace(CARE_TEAM_ID),
            key,
            {"note": case.note, "saved_at": key},
            index=["note"],
        )


def run_eval() -> list[dict]:
    store = build_memory_store()
    seed_episodes(store)

    results = []
    for case in CASES:
        hits = store.search(episode_namespace(CARE_TEAM_ID), query=case.query, limit=SEARCH_LIMIT)
        notes_in_order = [item.value["note"] for item in hits]
        found = case.note in notes_in_order
        rank = notes_in_order.index(case.note) + 1 if found else None
        results.append(
            {
                "id": case.id,
                "query": case.query,
                "expected_note": case.note,
                "found_in_top5": found,
                "rank": rank,
                "top_results": notes_in_order,
            }
        )
    return results


def print_report(results: list[dict]) -> dict:
    print(f"{'ID':<20} {'found top-5':<12} {'rank':<6}")
    for r in results:
        print(f"{r['id']:<20} {'YES' if r['found_in_top5'] else 'NO':<12} {r['rank'] or '-':<6}")

    n = len(results)
    passed = sum(r["found_in_top5"] for r in results)
    print()
    print(f"Recall (found in top-{SEARCH_LIMIT}): {passed}/{n} ({passed / n:.0%})")

    misses = [r for r in results if not r["found_in_top5"]]
    if misses:
        print()
        for r in misses:
            print(f"--- MISSED: {r['id']} ---")
            print("query:", r["query"])
            print("expected:", r["expected_note"])
            print("got instead:", r["top_results"])
            print()

    return {"passed": passed, "total": n, "cases": results}


if __name__ == "__main__":
    summary = print_report(run_eval())
    save_eval_summary("memory", summary)
