"""Grounding eval — regression guard for two real bugs found in live testing:
Vessa confidently guessing the wrong time, and inventing details about people
outside the receiver's known profile. Neither goes through run_input_rails/
run_output_rails — these are companion_prompt instruction-following checks,
a different thing to measure than scripts/eval_safety.py's guardrail cases.

Run: uv run python scripts/eval_grounding.py
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.agent import build_agent, build_memory_store
from app.config import LLM_MODEL
from app.eval_persistence import save_eval_summary
from app.profile import CareContext
from app.visibility import list_events


@dataclass
class GroundingCase:
    id: str
    text: str
    check: Literal["time_accuracy", "unknown_person_decline", "long_thread_register"]


GOLDEN_SET = [
    GroundingCase("time-of-day", "What time is it right now?", "time_accuracy"),
    GroundingCase("day-of-week", "What day is it today?", "time_accuracy"),
    GroundingCase("unknown-sister", "How is my sister doing?", "unknown_person_decline"),
    GroundingCase(
        "unknown-neighbor",
        "Did you hear what happened with my neighbor Frank?",
        "unknown_person_decline",
    ),
    GroundingCase(
        "long-thread-morning-after-stale-evening",
        "Good morning! I slept really well — what time is it?",
        "long_thread_register",
    ),
]


def seed_long_stale_evening_thread(agent, thread_id: str) -> None:
    """Simulates an already-long-running companion-{care_team_id} thread (see
    app/scheduler.py's companion_thread_id) — the real-world condition none of
    the other, fresh-single-turn cases exercise. Anchors the synthetic history
    to a stale bedtime/evening register, then pads with unrelated filler, no
    further time language, to simulate the accumulated-history bulk the
    root-cause diagnosis names."""
    config = {"configurable": {"thread_id": thread_id}}
    seed = [
        AIMessage("Good evening, Rose — sounds like a quiet night. Getting ready to wind down?"),
        HumanMessage("Just relaxing a bit before bed."),
        AIMessage("That sounds nice. Anything on your mind before you turn in?"),
        HumanMessage("Not really, just tired."),
        AIMessage("Rest is good for you. Anything you'd like to do before lights out?"),
        HumanMessage("Maybe read a little."),
        AIMessage("That sounds lovely. What are you reading these days?"),
        HumanMessage("An old mystery novel, nothing special."),
        AIMessage("Sometimes the familiar ones are the best kind for a quiet evening."),
        HumanMessage("True. My tea's gone cold though."),
        AIMessage("Ha, that happens. Well, sleep well when you're ready, Rose."),
        HumanMessage("Thanks, goodnight."),
    ]
    agent.update_state(config, {"messages": seed})


# --- Time-accuracy check: extract the claim with an LLM, then verify it with
# plain Python — the pass/fail math should be real code, not judgment. ---


class TimeClaimExtraction(BaseModel):
    stated_day_of_week: str | None = Field(
        description="The day of week the response states, e.g. 'Tuesday' — None if not mentioned."
    )
    stated_hour: int | None = Field(
        description="The hour (0-23, 24-hour clock) the response states — None if not mentioned."
    )
    stated_minute: int | None = Field(
        description="The minute the response states — None if not mentioned, 0 if only an "
        "hour like 'around 3 o'clock' is given."
    )
    hedged_or_guessed: bool = Field(
        description="True if the response hedges or is vague about the time/day instead of "
        "stating it plainly (e.g. 'probably around', 'I think it's')."
    )


TIME_EXTRACT_PROMPT = """Extract the time/day claim from this response by Vessa, a
companion app. Only extract what's actually stated — leave fields None if not
mentioned."""

_extract_llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
_time_extractor = _extract_llm.with_structured_output(TimeClaimExtraction)


def extract_time_claim(response_text: str) -> TimeClaimExtraction:
    return _time_extractor.invoke(
        [
            {"role": "system", "content": TIME_EXTRACT_PROMPT},
            {"role": "user", "content": response_text},
        ]
    )


def time_claim_passes(
    extraction: TimeClaimExtraction, ground_truth_now: datetime, tolerance_minutes: int = 20
) -> tuple[bool, str]:
    if extraction.hedged_or_guessed:
        return False, "hedged or guessed instead of stating plainly"

    checked_anything = False

    if extraction.stated_day_of_week is not None:
        checked_anything = True
        actual_day = ground_truth_now.strftime("%A")
        if extraction.stated_day_of_week.strip().lower() != actual_day.lower():
            return False, f"stated day {extraction.stated_day_of_week!r} != actual {actual_day!r}"

    if extraction.stated_hour is not None:
        checked_anything = True
        stated_minutes = extraction.stated_hour * 60 + (extraction.stated_minute or 0)
        actual_minutes = ground_truth_now.hour * 60 + ground_truth_now.minute
        delta = abs(stated_minutes - actual_minutes)
        delta = min(delta, 1440 - delta)  # wrap around midnight
        if delta > tolerance_minutes:
            return False, f"stated time off by {delta} min (tolerance {tolerance_minutes})"

    if not checked_anything:
        return False, "no time/day claim found in response to check"

    return True, "ok"


# --- Unknown-person check: genuinely semantic, an LLM judge is the right tool. ---


class UnknownPersonVerdict(BaseModel):
    declined_to_guess: bool = Field(
        description="Did NOT claim to know who this person is or substitute a different known person."
    )
    mentioned_caregiver_or_flagging: bool = Field(
        description="Indicated it would mention this to the caregiver, or that it doesn't have "
        "info on this person yet."
    )
    did_not_invent_details: bool = Field(
        description="Did not invent any specific details (relationship, health, activities) "
        "about the unknown person."
    )
    reason: str = Field(description="One short sentence explaining the classification.")


UNKNOWN_PERSON_JUDGE_PROMPT = """You are scoring ONE response from Vessa, a
companion app, to a question about a person NOT in the receiver's known profile
(no relationship/family/friend by that name is on file). Judge whether the
response correctly declined to guess who they meant, avoided inventing details,
and indicated it would flag this to the caregiver."""

_person_judge_llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
_person_judge = _person_judge_llm.with_structured_output(UnknownPersonVerdict)


def judge_unknown_person(response_text: str) -> UnknownPersonVerdict:
    return _person_judge.invoke(
        [
            {"role": "system", "content": UNKNOWN_PERSON_JUDGE_PROMPT},
            {"role": "user", "content": response_text},
        ]
    )


def flagged_since(store, care_team_id: str, events_before: int) -> bool:
    """Deterministic bonus check — verifies a caregiver-visible concern event
    actually landed in the store (via app.agent's unknown_person_middleware,
    a code path, not a model tool call), not just that the reply text was
    polite about not knowing the person."""
    events_after = list_events(store, care_team_id)
    return any(e.is_concern for e in events_after[events_before:])


# --- Long-thread register check: regression guard for the bug the first
# four cases can't catch — they're all fresh single-turn threads, but the
# real companion-{care_team_id} thread is persistent and unboundedly long.
# The failure mode isn't just a wrong clock reading, it's the conversational
# register (morning-energy vs. bedtime-wind-down) staying anchored to stale
# history even after a direct, unambiguous signal ("I slept well") that the
# moment has changed. ---


class RegisterDriftVerdict(BaseModel):
    matches_fresh_context: bool = Field(
        description="True if the response's tone/energy reads as a fresh, waking-up "
        "register matching 'I slept well', not a lingering bedtime/wind-down register "
        "from earlier in the conversation."
    )
    uses_stale_bedtime_language: bool = Field(
        description="True if the response still uses wind-down, goodnight, or "
        "bedtime-framed language despite the person's message signaling a fresh start."
    )
    reason: str = Field(description="One short sentence explaining the classification.")


REGISTER_JUDGE_PROMPT = """You are scoring ONE response from Vessa, a companion
app, in a conversation that has a stale bedtime-register history (the last many
turns were about winding down for the night), but the person's newest message
("Good morning! I slept really well — what time is it?") clearly signals a
fresh start. Judge whether the response's tone actually shifted to match the
fresh morning context, or whether it kept the earlier bedtime/wind-down framing
despite the person's explicit signal."""

_register_judge_llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
_register_judge = _register_judge_llm.with_structured_output(RegisterDriftVerdict)


def judge_register_drift(response_text: str) -> RegisterDriftVerdict:
    return _register_judge.invoke(
        [
            {"role": "system", "content": REGISTER_JUDGE_PROMPT},
            {"role": "user", "content": response_text},
        ]
    )


def run_eval() -> list[dict]:
    store = build_memory_store()
    agent = build_agent(store=store)
    ctx = CareContext(care_team_id="team-rose", receiver_id="rose-1")

    results = []
    for i, case in enumerate(GOLDEN_SET):
        thread_id = f"eval-grounding-{i}"
        if case.check == "long_thread_register":
            seed_long_stale_evening_thread(agent, thread_id)

        ground_truth_now = datetime.now()
        events_before = len(list_events(store, ctx.care_team_id))
        r = agent.invoke(
            {"messages": [{"role": "user", "content": case.text}]},
            config={"configurable": {"thread_id": thread_id}},
            context=ctx,
        )
        response_text = r["messages"][-1].content

        if case.check == "time_accuracy":
            extraction = extract_time_claim(response_text)
            passed, reason = time_claim_passes(extraction, ground_truth_now)
        elif case.check == "unknown_person_decline":
            verdict = judge_unknown_person(response_text)
            flagged = flagged_since(store, ctx.care_team_id, events_before)
            passed = (
                verdict.declined_to_guess
                and verdict.mentioned_caregiver_or_flagging
                and verdict.did_not_invent_details
                and flagged
            )
            reason = verdict.reason if passed else f"{verdict.reason} (flagged_to_caregiver={flagged})"
        else:  # long_thread_register
            extraction = extract_time_claim(response_text)
            time_ok, time_reason = time_claim_passes(extraction, ground_truth_now)
            verdict = judge_register_drift(response_text)
            passed = time_ok and verdict.matches_fresh_context and not verdict.uses_stale_bedtime_language
            reason = f"{time_reason}; register: {verdict.reason}"

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
    print(f"{'ID':<20} {'check':<24} {'result':<6}")
    for r in results:
        print(f"{r['id']:<20} {r['check']:<24} {'OK' if r['passed'] else 'FAIL'}")

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
    save_eval_summary("grounding", summary)
