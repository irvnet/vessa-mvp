"""Seed a believable, 'lived-in' demo state for Rose — so a demo doesn't open on
an empty (or test-junk-filled) app. Full reset + reseed: wipes the SQLite DB
(after backing it up), then writes a crafted set of memories, reminders, Today
events, and one short morning conversation, all drawn from Rose's own profile.

Mood: a good day with ONE gentle 'needs attention' signal (Biscuit off his food,
flagged to Linda) — enough to demo the attention path without alarm theater.

Run on the box that owns the live DB, with the service stopped so nothing else
holds the SQLite file:

    sudo systemctl stop vessa
    uv run python scripts/seed_demo.py --reset
    sudo systemctl start vessa

--reset is required — this is destructive (it wipes the DB first, keeping a
timestamped backup under data/backups/).
"""

import argparse
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage

from app.agent import build_agent, episode_namespace
from app.config import SQLITE_DB_PATH, load_env, now_local
from app.persistence import build_sqlite_saver, build_sqlite_store
from app.reminders import Reminder, ReminderStatus, reminder_namespace
from app.scheduler import companion_thread_id
from app.summary import daily_summary_namespace
from app.visibility import Event, EventType, event_namespace

CARE_TEAM_ID = "team-rose"
DB_FILES = ("", "-wal", "-shm")  # main db + WAL sidecars


def backup_db() -> Path | None:
    """Copy the current DB (and its WAL sidecars) to a timestamped backup so a
    reset is always recoverable. Returns the backup path, or None if no DB yet."""
    main = Path(SQLITE_DB_PATH)
    if not main.exists():
        return None
    backup_dir = main.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = backup_dir / f"vessa-{stamp}.db"
    for suffix in DB_FILES:
        src = Path(str(SQLITE_DB_PATH) + suffix)
        if src.exists():
            shutil.copy2(src, str(dest) + suffix)
    return dest


def wipe_db() -> None:
    for suffix in DB_FILES:
        p = Path(str(SQLITE_DB_PATH) + suffix)
        if p.exists():
            p.unlink()


# --- What Vessa remembers about Rose (episodic memory) ---
# (days_ago, note) — staggered so the recall/ordering reads naturally.
# Deliberately more than a demo strictly needs. Proactive check-ins sample from the
# most recent slice (app.agent.CHECKIN_EPISODE_POOL), so a thin history means every
# check-in opens on the same topic — with only nine, Vessa greeted Rose about her rose
# garden four times running. Breadth here is what makes "it remembers you" hold up over
# more than one exchange. Each one is written to be answerable later: a state that can
# have changed, so "how's that going now?" is a real question.
EPISODES = [
    (7, "Rose talked about her thirty years as a school librarian and the children who still write to her."),
    (7, "Rose said the corner shop changed hands and she misses the couple who ran it."),
    (6, "Rose watched a documentary about lighthouses that reminded her of a trip to Maine with Walt."),
    (6, "Rose's neighbour Dorothy brought round a plate of shortbread on Sunday."),
    (5, "Rose and her daughter Linda are planning a visit to the botanical garden."),
    (5, "Rose said Saturday's crossword was the hardest one in weeks and she left two clues unfinished."),
    (4, "Rose is looking forward to her son Mark visiting for her birthday next month."),
    (4, "Rose told the story of meeting Walt at a church dance in 1962 — one of her favourites."),
    (3, "Rose started a 1000-piece jigsaw puzzle of a lighthouse this week."),
    (3, "Rose has been sleeping better since she moved her armchair next to the window."),
    (3, "Rose mentioned the hallway light on her floor has been flickering."),
    (2, "Rose's cat Biscuit hasn't been eating much the last couple of days."),
    (2, "Rose mentioned her knee has been a little sore since the weekend."),
    (2, "Rose said the building elevator was out again last week and she took the stairs slowly."),
    (2, "Rose has been doing the crossword with her morning coffee most days this week."),
    (1, "Rose spent yesterday afternoon listening to her old Glenn Miller records."),
    (1, "Rose is proud of a new bloom on her balcony rose garden."),
    (1, "Rose got three answers before the contestants on her afternoon game show."),
    (1, "Rose said the weather turned and she hasn't been out on the balcony as much."),
]


def seed_episodes(store) -> int:
    now = datetime.now(timezone.utc)
    # minutes=i keeps every key unique even when two episodes share days_ago —
    # identical keys would silently overwrite each other (one memory clobbers
    # another), so this guarantees every episode lands distinctly.
    for i, (days_ago, note) in enumerate(EPISODES):
        key = (now - timedelta(days=days_ago, minutes=i)).isoformat()
        store.put(episode_namespace(CARE_TEAM_ID), key, {"note": note, "saved_at": key}, index=["note"])
    return len(EPISODES)


def seed_reminders(store) -> int:
    """Two already-acknowledged (the closed-loop win) + two still open. Open ones
    are due in the near future so they never read as 'missed' at demo time."""
    now = now_local()
    reminders = [
        Reminder(
            id=str(uuid4()), care_team_id=CARE_TEAM_ID, subject="Take morning vitamins",
            due_at=(now - timedelta(hours=4)).isoformat(), status=ReminderStatus.ACKNOWLEDGED.value,
            created_at=(now - timedelta(days=1)).isoformat(),
            acknowledged_at=(now - timedelta(hours=3, minutes=30)).isoformat(),
        ),
        Reminder(
            id=str(uuid4()), care_team_id=CARE_TEAM_ID, subject="Afternoon heart medication",
            due_at=(now - timedelta(hours=2)).isoformat(), status=ReminderStatus.ACKNOWLEDGED.value,
            created_at=(now - timedelta(days=1)).isoformat(),
            acknowledged_at=(now - timedelta(hours=1, minutes=55)).isoformat(),
        ),
        Reminder(
            id=str(uuid4()), care_team_id=CARE_TEAM_ID, subject="Water the rose garden",
            due_at=(now + timedelta(hours=1)).isoformat(), status=ReminderStatus.DELIVERED.value,
            created_at=(now - timedelta(hours=5)).isoformat(),
        ),
        Reminder(
            id=str(uuid4()), care_team_id=CARE_TEAM_ID, subject="Call Linda back this evening",
            due_at=(now + timedelta(hours=3)).isoformat(), status=ReminderStatus.PENDING.value,
            created_at=(now - timedelta(hours=2)).isoformat(),
        ),
    ]
    for r in reminders:
        store.put(reminder_namespace(CARE_TEAM_ID), r.id, r.__dict__, index=False)
    return len(reminders)


def seed_events(store) -> int:
    """Today's activity feed — relative to now so it always lands 'earlier today.'
    (hours_ago, minutes_ago, type, summary, is_concern)."""
    now = now_local()
    events = [
        (4, 0, EventType.CHECKIN_SENT.value, "Good morning check-in sent", False),
        (3, 30, EventType.REMINDER_ACKNOWLEDGED.value, "Acknowledged: Take morning vitamins", False),
        (1, 55, EventType.REMINDER_ACKNOWLEDGED.value, "Acknowledged: Afternoon heart medication", False),
        (1, 0, EventType.SIGNAL_NOTED.value, "Biscuit hasn't been eating much — flagged to Linda", True),
        (0, 30, EventType.REMINDER_DELIVERED.value, "Surfaced: Water the rose garden", False),
    ]
    for hrs, mins, etype, summary, concern in events:
        at = (now - timedelta(hours=hrs, minutes=mins)).isoformat()
        event = Event(
            id=str(uuid4()), care_team_id=CARE_TEAM_ID, type=etype,
            summary=summary, at=at, is_concern=concern,
        )
        store.put(event_namespace(CARE_TEAM_ID), event.id, event.__dict__, index=False)
    return len(events)


# Guardrail activity for the /proof page — dated in the PAST (>24h) on purpose:
# it populates /proof's Guardrail Activity panel (which reads all events) without
# cluttering today's calm care-team feed (which reads only today's). Kept light
# and non-alarming: everyday redirects + one output-repair, no seeded emergency.
# (hours_ago, type, summary, is_concern)
GUARDRAIL_EVENTS = [
    (52, EventType.GUARDRAIL_REDIRECTED.value, "medical-advice: asked whether she should take an extra blood-pressure pill", False),
    (30, EventType.GUARDRAIL_REDIRECTED.value, "self-diagnosis: read online what her symptoms might mean and wanted it confirmed", False),
    (27, EventType.GUARDRAIL_OUTPUT_REPAIRED.value, "repaired: redacted 1 phone number from a draft reply", False),
    (26, EventType.GUARDRAIL_REDIRECTED.value, "injection: a message tried to override Vessa's instructions", False),
]


def seed_guardrail_events(store) -> int:
    now = now_local()
    for hrs, etype, summary, concern in GUARDRAIL_EVENTS:
        at = (now - timedelta(hours=hrs)).isoformat()
        event = Event(
            id=str(uuid4()), care_team_id=CARE_TEAM_ID, type=etype,
            summary=summary, at=at, is_concern=concern,
        )
        store.put(event_namespace(CARE_TEAM_ID), event.id, event.__dict__, index=False)
    return len(GUARDRAIL_EVENTS)


# Pre-written so the caregiver's Today banner opens on a great line immediately,
# rather than the first page load paying for a live LLM call. event_count must
# match the number of today's events so app.summary treats it as a fresh cache
# hit; once a caregiver acks a reminder live, the count changes and it refreshes.
DAILY_SUMMARY = (
    "Rose seems steady today — she took her morning vitamins and afternoon "
    "medication, was in good spirits chatting about her lighthouse puzzle, and "
    "mentioned Biscuit's been a little off his food, which I've let Linda know."
)


def seed_daily_summary(store, today_event_count: int) -> None:
    store.put(
        daily_summary_namespace(CARE_TEAM_ID),
        now_local().date().isoformat(),
        {"summary": DAILY_SUMMARY, "generated_at": now_local().isoformat(), "event_count": today_event_count},
        index=False,
    )


# One short, warm morning exchange — cohesive with the memories and events above
# (Biscuit, the vitamins, the puzzle). Ends on Vessa so the scheduler won't
# immediately stack another check-in on top of it.
CONVERSATION = [
    AIMessage("Good morning, Rose. The light looks lovely on the balcony today — did you sleep alright?"),
    HumanMessage("Morning. Slept okay. Biscuit's been off his food though, I'm a little worried about him."),
    AIMessage(
        "I'm sorry Biscuit's not quite himself — I've made a note so Linda can keep an eye on him "
        "with you. Did you still want your morning vitamins? They're by the kettle."
    ),
    HumanMessage("Oh, yes — just took them, thank you."),
    AIMessage("Wonderful, that's them done for the day. How's the lighthouse puzzle coming along?"),
    HumanMessage("Slowly! All that sky is impossible."),
    AIMessage("Ha — the sky's always the hardest part. You'll get there, Rose."),
]


def seed_conversation(store, saver) -> int:
    agent = build_agent(store=store, checkpointer=saver)
    config = {"configurable": {"thread_id": companion_thread_id(CARE_TEAM_ID)}}
    agent.update_state(config, {"messages": CONVERSATION})
    return len(CONVERSATION)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a lived-in demo state for Rose.")
    parser.add_argument(
        "--reset", action="store_true",
        help="Required. Backs up then WIPES the DB before seeding (a clean, known-good state).",
    )
    args = parser.parse_args()

    if not args.reset:
        print("Refusing to run without --reset (this is destructive). See the module docstring.", file=sys.stderr)
        return 2

    load_env()  # OPENAI_API_KEY — episodes are embedded on write

    backup = backup_db()
    print(f"Backed up existing DB -> {backup}" if backup else "No existing DB to back up.")
    wipe_db()
    print("Wiped DB (fresh schema will be created).")

    store = build_sqlite_store()
    saver = build_sqlite_saver()

    n_ep = seed_episodes(store)
    n_rem = seed_reminders(store)
    n_ev = seed_events(store)
    n_gr = seed_guardrail_events(store)
    seed_daily_summary(store, today_event_count=n_ev)
    n_msg = seed_conversation(store, saver)

    print(
        f"Seeded: {n_ep} memories, {n_rem} reminders, {n_ev} Today events, "
        f"{n_gr} guardrail events (past days), a daily summary, {n_msg}-message conversation."
    )
    print("Today reads '⚠️ Needs attention' (Biscuit signal); /proof shows guardrail activity. Restart the service now.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
