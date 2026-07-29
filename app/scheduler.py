"""C1 proactivity — the real scheduler. A separate background job (APScheduler),
not part of the agent graph: on an interval, generates a check-in per receiver and
pushes it into that receiver's stable companion thread. Interval is short here for
local demo visibility — real deployment would tune cadence per receiver/time-of-day,
which is out of MVP scope."""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.messages import AIMessage

from app.agent import generate_checkin

logger = logging.getLogger(__name__)

CHECKIN_INTERVAL_MINUTES = 2


def companion_thread_id(care_team_id: str) -> str:
    """One stable, ongoing conversation thread per receiver — not a fresh one per
    page load. The scheduler and the live companion surface both target this
    same thread so a proactive push actually lands somewhere being watched."""
    return f"companion-{care_team_id}"


def _should_checkin(agent, thread_id: str) -> bool:
    """Skip firing if the last message is already an unanswered check-in — avoid
    piling up back-to-back proactive messages before the receiver has replied."""
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    if not messages:
        return True
    return messages[-1].type != "ai"


def run_checkin_job(agent, store, care_team_id: str) -> None:
    thread_id = companion_thread_id(care_team_id)
    if not _should_checkin(agent, thread_id):
        logger.info("Scheduler: skipping check-in for %s — awaiting a reply already", care_team_id)
        return

    text = generate_checkin(care_team_id, store=store)
    agent.update_state({"configurable": {"thread_id": thread_id}}, {"messages": [AIMessage(content=text)]})
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
