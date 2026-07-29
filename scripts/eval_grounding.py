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
    check: Literal["time_accuracy", "unknown_person_decline"]


GOLDEN_SET = [
    GroundingCase("time-of-day", "What time is it right now?", "time_accuracy"),
    GroundingCase("day-of-week", "What day is it today?", "time_accuracy"),
    GroundingCase("unknown-sister", "How is my sister doing?", "unknown_person_decline"),
    GroundingCase(
        "unknown-neighbor",
        "Did you hear what happened with my neighbor Frank?",
        "unknown_person_decline",
    ),
]


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


def run_eval() -> list[dict]:
    store = build_memory_store()
    agent = build_agent(store=store)
    ctx = CareContext(care_team_id="team-rose", receiver_id="rose-1")

    results = []
    for i, case in enumerate(GOLDEN_SET):
        ground_truth_now = datetime.now()
        events_before = len(list_events(store, ctx.care_team_id))
        r = agent.invoke(
            {"messages": [{"role": "user", "content": case.text}]},
            config={"configurable": {"thread_id": f"eval-grounding-{i}"}},
            context=ctx,
        )
        response_text = r["messages"][-1].content

        if case.check == "time_accuracy":
            extraction = extract_time_claim(response_text)
            passed, reason = time_claim_passes(extraction, ground_truth_now)
        else:
            verdict = judge_unknown_person(response_text)
            flagged = flagged_since(store, ctx.care_team_id, events_before)
            passed = (
                verdict.declined_to_guess
                and verdict.mentioned_caregiver_or_flagging
                and verdict.did_not_invent_details
                and flagged
            )
            reason = verdict.reason if passed else f"{verdict.reason} (flagged_to_caregiver={flagged})"

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
