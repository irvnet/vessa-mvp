"""C3 — caregiver visibility ("Today"). Event log + Signal (surfaced concern) —
largely a byproduct of C1+C2's own data, per Care-Companion-Feature-Roadmap.
Status badge + timeline + surfaced signals, not a full clinical dashboard."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from langgraph.store.memory import InMemoryStore


class EventType(str, Enum):
    CHECKIN_SENT = "checkin_sent"
    REMINDER_CREATED = "reminder_created"
    REMINDER_DELIVERED = "reminder_delivered"
    REMINDER_ACKNOWLEDGED = "reminder_acknowledged"
    SIGNAL_NOTED = "signal_noted"
    GUARDRAIL_REDIRECTED = "guardrail_redirected"
    GUARDRAIL_ESCALATED = "guardrail_escalated"
    GUARDRAIL_OUTPUT_REPAIRED = "guardrail_output_repaired"


@dataclass
class Event:
    id: str
    care_team_id: str
    type: str
    summary: str
    at: str  # ISO timestamp
    is_concern: bool = False


def event_namespace(care_team_id: str) -> tuple[str, str]:
    return (care_team_id, "event")


def log_event(
    store: InMemoryStore, care_team_id: str, event_type: str, summary: str, is_concern: bool = False
) -> Event:
    event_id = str(uuid.uuid4())
    event = Event(
        id=event_id,
        care_team_id=care_team_id,
        type=event_type,
        summary=summary,
        at=datetime.now().isoformat(),
        is_concern=is_concern,
    )
    store.put(event_namespace(care_team_id), event_id, event.__dict__, index=False)
    return event


def list_events(store: InMemoryStore, care_team_id: str, since: datetime | None = None) -> list[Event]:
    items = store.search(event_namespace(care_team_id))
    events = [Event(**item.value) for item in items]
    if since is not None:
        events = [e for e in events if datetime.fromisoformat(e.at) >= since]
    return sorted(events, key=lambda e: e.at)


def todays_events(store: InMemoryStore, care_team_id: str) -> list[Event]:
    start_of_today = datetime.combine(date.today(), datetime.min.time())
    return list_events(store, care_team_id, since=start_of_today)


def status_badge(events: list[Event]) -> str:
    """Any unresolved concern today -> attention; otherwise ok. Simple, not clinical."""
    return "attention" if any(e.is_concern for e in events) else "ok"
