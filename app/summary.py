"""Vessa's one-line daily summary for the caregiver's Today view — a warm, human
sentence a busy adult child can read at a glance, instead of parsing a timeline.
Written by the model over the day's activity + what's recently on the receiver's
mind, then cached per day and only regenerated when the day's event count changes
(so dashboard polling doesn't spam the LLM, but a live reminder-ack refreshes it)."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import LLM_MODEL, load_env, now_local
from app.profile import get_profile
from app.visibility import Event

load_env()

_summary_llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)

SUMMARY_PROMPT = """You are Vessa, an AI companion, writing ONE sentence for {name}'s
family caregiver to glance at on their phone. Summarize how {name}'s day is going,
warmly and in plain language — mention 1-3 concrete things from what's below (a
reminder taken, something they talked about, their spirits). If something's worth
attention, note it gently and plainly — never clinical, never alarming. Write it
the way a kind person who spent the day with {name} would put it, not a status
report. One sentence, no preamble."""


def daily_summary_namespace(care_team_id: str) -> tuple[str, str]:
    return (care_team_id, "daily_summary")


def _today_key() -> str:
    return now_local().date().isoformat()


def _recent_episodes(store, care_team_id: str, limit: int = 4) -> list[str]:
    items = store.search((care_team_id, "episode"))
    recent = sorted(items, key=lambda it: it.value.get("saved_at", ""), reverse=True)[:limit]
    return [it.value["note"] for it in recent]


def _render(events: list[Event], episodes: list[str]) -> str:
    ev = "\n".join(
        f"- {e.summary}" + (" (worth attention)" if e.is_concern else "") for e in events
    ) or "- (nothing logged yet today)"
    mind = "\n".join(f"- {n}" for n in episodes) or "- (nothing noted recently)"
    return f"Today's activity:\n{ev}\n\nRecently on their mind:\n{mind}"


def generate_daily_summary(store, care_team_id: str, events: list[Event]) -> str:
    profile = get_profile(care_team_id)
    episodes = _recent_episodes(store, care_team_id)
    resp = _summary_llm.invoke(
        [
            {"role": "system", "content": SUMMARY_PROMPT.format(name=profile.name)},
            {"role": "user", "content": _render(events, episodes)},
        ]
    )
    return str(resp.content).strip()


def get_or_refresh_daily_summary(store, care_team_id: str, events: list[Event]) -> str:
    """Cached per day; regenerated only when missing or the day's event count changed
    (a live reminder-ack adds an event → the summary refreshes on the next read)."""
    ns = daily_summary_namespace(care_team_id)
    key = _today_key()
    cached = store.get(ns, key)
    if cached is not None and cached.value.get("event_count") == len(events):
        return cached.value["summary"]

    summary = generate_daily_summary(store, care_team_id, events)
    store.put(
        ns, key,
        {"summary": summary, "generated_at": now_local().isoformat(), "event_count": len(events)},
        index=False,
    )
    return summary
