"""Reminder-loop eval — C2 is the closed loop (caregiver sets it → Vessa surfaces it
warmly → the receiver confirms → the caregiver sees the acknowledgment), and until now
nothing measured it. Each case guards a specific way that loop breaks:

- surfaced warmly: the prompt forbids robotic "REMINDER: ..." phrasing (app/agent.py) —
  a medication nudge that reads like a system alert isn't a companion.
- overdue still surfaced: the real bug. A reminder went invisible once its due time
  passed, which is precisely the moment a medication reminder matters most. Fixed in
  _open_reminders (app/reminders.py) — anything short of acknowledged stays open.
- acknowledged on confirmation: checked against the store, not the reply text. The loop
  only closes if the status actually flips.
- no invention: with nothing open, Vessa must not manufacture a reminder.

Run: uv run python scripts/eval_reminders.py
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.agent import build_agent, build_memory_store
from app.config import LLM_MODEL, now_local
from app.eval_persistence import save_eval_summary
from app.profile import CareContext
from app.reminders import ReminderStatus, create_reminder, effective_status, list_reminders


@dataclass
class ReminderCase:
    id: str
    text: str
    check: Literal["surfaced_warmly", "acknowledged", "no_invention"]
    # Hours relative to now: negative seeds an overdue reminder, positive a due-soon one,
    # None seeds nothing at all.
    seed_due_in_hours: float | None = None
    seed_subject: str = "take her blood pressure pills"


GOLDEN_SET = [
    ReminderCase(
        "reminder-surfaced-warmly",
        "Good morning! It's a nice day out there.",
        "surfaced_warmly",
        seed_due_in_hours=-0.25,
    ),
    # The regression: overdue must not mean invisible.
    ReminderCase(
        "reminder-overdue-still-surfaced",
        "I've just been pottering about this morning.",
        "surfaced_warmly",
        seed_due_in_hours=-3,
    ),
    ReminderCase(
        "reminder-acknowledged-on-confirmation",
        "Oh yes — I already took my pills, thank you for asking.",
        "acknowledged",
        seed_due_in_hours=-0.25,
    ),
    ReminderCase(
        "no-reminder-none-invented",
        "Is there anything I'm supposed to be doing today?",
        "no_invention",
        seed_due_in_hours=None,
    ),
]


# --- Surfacing check: whether it was mentioned, and whether it sounded human. ---


class SurfacingVerdict(BaseModel):
    mentioned_the_reminder: bool = Field(
        description="Did the response bring up the reminder subject (e.g. taking pills) at all?"
    )
    sounded_like_a_friend: bool = Field(
        description="Was it woven into warm conversation, rather than announced like a "
        "system alert (e.g. 'REMINDER:', 'ALERT:', a bulleted task list, or an id/timestamp)?"
    )
    leaked_internals: bool = Field(
        description="Did it expose anything technical — an id, an ISO timestamp, a status "
        "word like 'pending' or 'delivered', or code-like formatting?"
    )
    reason: str = Field(description="One short sentence explaining the classification.")


SURFACING_JUDGE_PROMPT = """You are scoring ONE response from Vessa, a companion app for
an older adult. A reminder set by her caregiver is currently open and due. Judge whether
the response brought that reminder up, whether it did so as a warm, natural mention the
way a friend would nudge, and whether it leaked any internal detail (ids, timestamps,
status words, code-like formatting)."""

_surfacing_judge = ChatOpenAI(model=LLM_MODEL, temperature=0).with_structured_output(
    SurfacingVerdict
)


class InventionVerdict(BaseModel):
    invented_a_reminder: bool = Field(
        description="Did the response claim there is a specific task, medication, or "
        "appointment she needs to do, when in fact nothing is on file?"
    )
    reason: str = Field(description="One short sentence explaining the classification.")


INVENTION_JUDGE_PROMPT = """You are scoring ONE response from Vessa, a companion app for
an older adult who asked whether she has anything to do today. There are NO reminders on
file. Judge whether the response invented a specific task, medication, or appointment.
Saying there's nothing scheduled, or offering to check with her caregiver, is correct."""

_invention_judge = ChatOpenAI(model=LLM_MODEL, temperature=0).with_structured_output(
    InventionVerdict
)


def run_eval() -> list[dict]:
    results = []
    for i, case in enumerate(GOLDEN_SET):
        # A fresh store per case — reminders are stateful, and one case's
        # acknowledgment must not change what the next case sees.
        store = build_memory_store()
        agent = build_agent(store=store)
        ctx = CareContext(care_team_id="team-rose", receiver_id="rose-1")

        seeded = None
        if case.seed_due_in_hours is not None:
            seeded = create_reminder(
                store,
                ctx.care_team_id,
                case.seed_subject,
                now_local() + timedelta(hours=case.seed_due_in_hours),
            )

        r = agent.invoke(
            {"messages": [{"role": "user", "content": case.text}]},
            config={"configurable": {"thread_id": f"eval-reminders-{i}"}},
            context=ctx,
        )
        response_text = r["messages"][-1].content

        if case.check == "surfaced_warmly":
            verdict = _surfacing_judge.invoke(
                [
                    {"role": "system", "content": SURFACING_JUDGE_PROMPT},
                    {"role": "user", "content": response_text},
                ]
            )
            passed = (
                verdict.mentioned_the_reminder
                and verdict.sounded_like_a_friend
                and not verdict.leaked_internals
            )
            reason = verdict.reason
        elif case.check == "acknowledged":
            # Deterministic: the loop closes in the store or it doesn't close at all.
            assert seeded is not None
            current = next(
                (x for x in list_reminders(store, ctx.care_team_id) if x.id == seeded.id), None
            )
            status = effective_status(current) if current else "missing"
            passed = status == ReminderStatus.ACKNOWLEDGED.value
            reason = f"status after confirmation: {status}"
        else:  # no_invention
            verdict = _invention_judge.invoke(
                [
                    {"role": "system", "content": INVENTION_JUDGE_PROMPT},
                    {"role": "user", "content": response_text},
                ]
            )
            passed = not verdict.invented_a_reminder
            reason = verdict.reason

        results.append(
            {
                "id": case.id,
                "check": case.check,
                "passed": passed,
                "reason": reason,
                "response": response_text,
            }
        )

    return results


def print_report(results: list[dict]) -> dict:
    print(f"{'ID':<38} {'check':<18} {'result':<6}")
    for r in results:
        print(f"{r['id']:<38} {r['check']:<18} {'OK' if r['passed'] else 'FAIL'}")

    n = len(results)
    passed = sum(r["passed"] for r in results)
    print()
    print(f"Passed: {passed}/{n} ({passed / n:.0%})")

    flagged = [r for r in results if not r["passed"]]
    if flagged:
        print()
        for r in flagged:
            print(f"--- FLAGGED: {r['id']} ---")
            print("reason:", r["reason"])
            print("response:", r["response"])
            print()

    return {"passed": passed, "total": n, "cases": results}


if __name__ == "__main__":
    summary = print_report(run_eval())
    save_eval_summary("reminders", summary)
