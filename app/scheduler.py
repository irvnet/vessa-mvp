"""C1 proactivity — the real scheduler. A separate background job (APScheduler),
not part of the agent graph: on an interval, generates a check-in per receiver and
pushes it into that receiver's stable companion thread. Interval is short here for
local demo visibility — real deployment would tune cadence per receiver/time-of-day,
which is out of MVP scope."""

import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.messages import AIMessage

from app.agent import generate_checkin
from app.config import now_local

logger = logging.getLogger(__name__)

# Short by default for demo visibility. Raise it via the env var when rehearsing, so a
# long run-through doesn't nudge the receiver every couple of minutes.
CHECKIN_INTERVAL_MINUTES = int(os.getenv("CHECKIN_INTERVAL_MINUTES", "2"))

# Marks an AIMessage as a proactive push rather than a reply. Without it the two are
# indistinguishable in the thread, which is what broke _should_checkin.
PROACTIVE_KEY = "proactive_checkin"
PROACTIVE_AT = "proactive_at"

# How long an unanswered check-in suppresses the next one. Without a ceiling a single
# ignored nudge silences Vessa forever — which is both wrong for someone who may simply
# have walked away from the tablet, and a trap on stage: open the app with a check-in
# still pending from rehearsal and nothing ever fires.
FOLLOWUP_AFTER_MINUTES = int(os.getenv("CHECKIN_FOLLOWUP_MINUTES", "10"))


def proactive_message(text: str) -> AIMessage:
    return AIMessage(
        content=text,
        additional_kwargs={PROACTIVE_KEY: True, PROACTIVE_AT: now_local().isoformat()},
    )


def companion_thread_id(care_team_id: str) -> str:
    """One stable, ongoing conversation thread per receiver — not a fresh one per
    page load. The scheduler and the live companion surface both target this
    same thread so a proactive push actually lands somewhere being watched."""
    return f"companion-{care_team_id}"


def _should_checkin(agent, thread_id: str) -> bool:
    """Skip firing only if the last proactive check-in is still unanswered — the point
    is not to stack nudges before the receiver has had a chance to reply.

    This used to test `messages[-1].type != "ai"`, which silently disabled the whole
    scheduler: a reply to the receiver is an AIMessage too, so after any exchange at all
    the last message was always "ai" and the job skipped forever. Check-ins are tagged
    at push time (PROACTIVE_KEY) so the two can actually be told apart."""
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    for message in reversed(messages):
        if message.type == "human":
            return True  # she's spoken since the last check-in — not stacking
        if message.type == "ai" and message.additional_kwargs.get(PROACTIVE_KEY):
            # An unanswered push holds the next one off, but only for a while.
            pushed_at = message.additional_kwargs.get(PROACTIVE_AT)
            if not pushed_at:
                return True  # pushed before pushes were timestamped — definitionally old
            age = now_local() - datetime.fromisoformat(pushed_at)
            return age >= timedelta(minutes=FOLLOWUP_AFTER_MINUTES)
    return True


def run_checkin_job(agent, store, care_team_id: str) -> None:
    thread_id = companion_thread_id(care_team_id)
    if not _should_checkin(agent, thread_id):
        logger.info("Scheduler: skipping check-in for %s — awaiting a reply already", care_team_id)
        return

    text = generate_checkin(care_team_id, store=store)
    agent.update_state({"configurable": {"thread_id": thread_id}}, {"messages": [proactive_message(text)]})
    logger.info("Scheduler: pushed check-in for %s: %s", care_team_id, text)


def start_scheduler(agent, store, care_team_ids: list[str]) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    for care_team_id in care_team_ids:
        scheduler.add_job(
            run_checkin_job,
            "interval",
            minutes=CHECKIN_INTERVAL_MINUTES,
            args=[agent, store, care_team_id],
            id=f"checkin-{care_team_id}",
            next_run_time=datetime.now() + timedelta(minutes=CHECKIN_INTERVAL_MINUTES),
        )
    scheduler.start()
    logger.info(
        "Scheduler started — check-in every %d min for %s", CHECKIN_INTERVAL_MINUTES, care_team_ids
    )
    return scheduler
