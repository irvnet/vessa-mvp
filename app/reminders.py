"""Reminder domain + companion-side tool — C2 (scheduled reminder, closed loop).
Care-Companion-Naming: Reminder { subject, dueAt, status: Pending·Delivered·
Acknowledged·Missed }. Caregiver produces reminders (plain REST — the Care Team
view is thin, no agent needed there yet); the companion surfaces + acknowledges
them (this is the receiver-scoped verb)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from langchain.tools import ToolRuntime, tool
from langgraph.store.memory import InMemoryStore

from app.profile import CareContext
from app.visibility import EventType, log_event


class ReminderStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    MISSED = "missed"


@dataclass
class Reminder:
    id: str
    care_team_id: str
    subject: str
    due_at: str  # ISO timestamp, naive local time (MVP — no timezone handling yet)
    status: str
    created_at: str
    acknowledged_at: str | None = None


def reminder_namespace(care_team_id: str) -> tuple[str, str]:
    return (care_team_id, "reminder")


def create_reminder(store: InMemoryStore, care_team_id: str, subject: str, due_at: datetime) -> Reminder:
    reminder_id = str(uuid.uuid4())
    reminder = Reminder(
        id=reminder_id,
        care_team_id=care_team_id,
        subject=subject.strip(),
        due_at=due_at.isoformat(),
        status=ReminderStatus.PENDING.value,
        created_at=datetime.now().isoformat(),
    )
    store.put(reminder_namespace(care_team_id), reminder_id, reminder.__dict__, index=False)
    log_event(store, care_team_id, EventType.REMINDER_CREATED.value, f"Reminder set: {reminder.subject}")
    return reminder


def _load_all(store: InMemoryStore, care_team_id: str) -> list[Reminder]:
    items = store.search(reminder_namespace(care_team_id))
    return [Reminder(**item.value) for item in items]


def effective_status(reminder: Reminder, now: datetime | None = None) -> str:
    """Missed is computed at read-time, not stored — due_at passed + never acknowledged."""
    if reminder.status == ReminderStatus.ACKNOWLEDGED.value:
        return reminder.status
    now = now or datetime.now()
    if datetime.fromisoformat(reminder.due_at) < now:
        return ReminderStatus.MISSED.value
    return reminder.status


def list_reminders(store: InMemoryStore, care_team_id: str) -> list[Reminder]:
    return sorted(_load_all(store, care_team_id), key=lambda r: r.due_at)


def mark_delivered(store: InMemoryStore, care_team_id: str, reminder_id: str) -> None:
    reminders = {r.id: r for r in _load_all(store, care_team_id)}
    reminder = reminders.get(reminder_id)
    if reminder is None or reminder.status != ReminderStatus.PENDING.value:
        return
    reminder.status = ReminderStatus.DELIVERED.value
    store.put(reminder_namespace(care_team_id), reminder_id, reminder.__dict__, index=False)
    log_event(store, care_team_id, EventType.REMINDER_DELIVERED.value, f"Surfaced: {reminder.subject}")


def acknowledge(store: InMemoryStore, care_team_id: str, reminder_id: str) -> Reminder:
    reminders = {r.id: r for r in _load_all(store, care_team_id)}
    reminder = reminders[reminder_id]
    reminder.status = ReminderStatus.ACKNOWLEDGED.value
    reminder.acknowledged_at = datetime.now().isoformat()
    store.put(reminder_namespace(care_team_id), reminder_id, reminder.__dict__, index=False)
    log_event(store, care_team_id, EventType.REMINDER_ACKNOWLEDGED.value, f"Acknowledged: {reminder.subject}")
    return reminder


def update_reminder(
    store: InMemoryStore,
    care_team_id: str,
    reminder_id: str,
    subject: str | None = None,
    due_at: datetime | None = None,
) -> Reminder:
    reminders = {r.id: r for r in _load_all(store, care_team_id)}
    reminder = reminders[reminder_id]
    if subject is not None:
        reminder.subject = subject.strip()
    if due_at is not None:
        reminder.due_at = due_at.isoformat()
    store.put(reminder_namespace(care_team_id), reminder_id, reminder.__dict__, index=False)
    return reminder


def delete_reminder(store: InMemoryStore, care_team_id: str, reminder_id: str) -> None:
    store.delete(reminder_namespace(care_team_id), reminder_id)


# Stand-in for real push/SMS/email delivery — an in-memory feed the Care Team
# view can read. Real delivery channel is a later integration, not MVP scope.
CAREGIVER_NOTIFICATIONS: dict[str, list[dict]] = {}


def notify_caregiver(care_team_id: str, message: str) -> None:
    CAREGIVER_NOTIFICATIONS.setdefault(care_team_id, []).append(
        {"message": message, "at": datetime.now().isoformat()}
    )


def _open_reminders(reminders: list[Reminder]) -> list[Reminder]:
    """Anything short of acknowledged is still open — including missed. A late
    'yes I finally took them' should still count; overdue must not mean invisible."""
    return [r for r in reminders if effective_status(r) != ReminderStatus.ACKNOWLEDGED.value]


def format_reminders_for_prompt(reminders: list[Reminder]) -> str:
    open_reminders = _open_reminders(reminders)
    if not open_reminders:
        return "(no open reminders)"
    return "\n".join(
        f"- {r.subject} (due {r.due_at}, status: {effective_status(r)}, id={r.id})"
        for r in open_reminders
    )


def find_best_match(reminders: list[Reminder], subject_hint: str) -> Reminder | None:
    """Simple substring match against open reminders — the receiver won't know IDs."""
    hint = subject_hint.lower().strip()
    open_reminders = _open_reminders(reminders)
    for r in open_reminders:
        if hint in r.subject.lower() or r.subject.lower() in hint:
            return r
    return open_reminders[0] if len(open_reminders) == 1 else None


@tool
def acknowledge_reminder(subject_hint: str, runtime: ToolRuntime[CareContext]) -> str:
    """Mark a reminder as done when the person confirms they've completed it — e.g.
    they say 'yes I took my vitamins.' subject_hint should be a short phrase matching
    what the reminder was about."""
    assert runtime.store is not None
    care_team_id = runtime.context.care_team_id
    reminders = list_reminders(runtime.store, care_team_id)
    match = find_best_match(reminders, subject_hint)
    if match is None:
        return "I don't see an open reminder matching that — no worries either way."

    acknowledge(runtime.store, care_team_id, match.id)
    notify_caregiver(care_team_id, f"Acknowledged: {match.subject}")
    return f"Got it, marked '{match.subject}' as done."
