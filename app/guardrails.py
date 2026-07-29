"""Input/output safety rails for Vessa — the medical boundary that must never be
crossed. Deterministic regex rails run first (fast, no LLM cost, catch the clearest
emergencies + injection attempts); a structured-output LLM verdict catches judgment
calls (self-diagnosis, advice-seeking) regex can't reliably phrase-match.
Design: Care-Companion-Safety-and-Evals.md — exposed to medical info is fine,
giving medical advice never is."""

import re
from dataclasses import dataclass
from typing import Literal

from langchain.agents.middleware import AgentState, after_model, before_model
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from app.config import LLM_MODEL, load_env
from app.visibility import EventType, log_event

load_env()


@dataclass
class RailDecision:
    action: Literal["allow", "redirect", "escalate"]
    rail: str
    reason: str
    message: str = ""


# --- Input rails: deterministic (fast, no LLM call) ---

EMERGENCY_PATTERNS = [
    r"chest\s+pain",
    r"(not|stopped|trouble|can'?t)\s+breath",
    r"(fell|fallen)\b.{0,30}(can'?t|cannot|unable)\s+(get\s+up|move)",
    r"unconscious|unresponsive|not\s+waking\s+up|passed\s+out",
    r"severe\s+bleed|bleeding\s+(won'?t|will\s+not)\s+stop",
    r"(face|mouth)\s+(drooping|numb)|slurred\s+speech",
    r"want(ed)?\s+to\s+(die|kill\s+myself|end\s+it)",
    r"took\s+too\s+many\s+(pills|medication)",
]

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"(reveal|print|show)\s+(your\s+)?(system\s+)?prompt",
    r"you\s+are\s+now\s+(a|an|in)\b",
    r"pretend\s+(to\s+be|you\s+are)",
    r"\bjailbreak\b",
    r"do\s+anything\s+now",
]

EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.-]+"
PHONE_PATTERN = r"(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"

EMERGENCY_MESSAGE = (
    "This sounds serious, and I'm not the right help for it. Please call 911 or "
    "your emergency line right now — if someone's with you, ask them to help too. "
    "I'll make sure your care team knows."
)

INJECTION_MESSAGE = (
    "I'm not able to do that. Is there something I can help you with as your companion?"
)


def first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return pattern
    return None


def redact_pii(text: str) -> tuple[str, int]:
    redacted, n_emails = re.subn(EMAIL_PATTERN, "[REDACTED_EMAIL]", text)
    redacted, n_phones = re.subn(PHONE_PATTERN, "[REDACTED_PHONE]", redacted)
    return redacted, n_emails + n_phones


def run_deterministic_input_rails(text: str) -> RailDecision | None:
    """Fast regex checks. None means nothing deterministic fired — fall through
    to the LLM judgment call."""
    if pattern := first_match(EMERGENCY_PATTERNS, text):
        return RailDecision("escalate", "emergency", f"matched {pattern!r}", EMERGENCY_MESSAGE)
    if pattern := first_match(INJECTION_PATTERNS, text):
        return RailDecision("redirect", "injection", f"matched {pattern!r}", INJECTION_MESSAGE)
    return None


# --- Input rails: LLM judgment call (phrasing regex can't reliably catch) ---


class MedicalVerdict(BaseModel):
    """Judgment call on one message from the care receiver."""

    is_emergency: bool = Field(
        description="A genuine acute, in-progress medical/safety emergency — not a "
        "calm mention of a chronic condition."
    )
    seeking_medical_advice: bool = Field(
        description="Explicitly ASKING a question or requesting guidance about a "
        "diagnosis, treatment, or medication/dosage (e.g. 'what should I do', "
        "'should I take X', 'is this serious'). A bare statement or observation of "
        "a symptom with no question attached is NOT this — that's just information, "
        "and the companion should be free to acknowledge and log it."
    )
    self_diagnosing: bool = Field(
        description="Reciting internet-researched self-diagnosis AND explicitly "
        "asking it to be confirmed or debated (e.g. 'don't you think that's what I "
        "have?'). Merely mentioning something they read is not enough on its own."
    )
    reason: str = Field(description="One short sentence explaining the classification.")


MEDICAL_GUARD_PROMPT = """You are a safety classifier for Vessa, a companion for an
older adult living independently. Classify the person's message. Emergencies are
acute, urgent, in-progress situations, not calm mentions of an existing condition.
Medical-advice-seeking and self-diagnosing BOTH require an explicit question or ask
directed at Vessa — not just the presence of symptom or health language. A bare
statement like "my knee has been hurting" with no question is safe informational
content the companion should acknowledge and log, NOT a guardrail case. Most
messages are none of these — small talk, preferences, calm updates, and plain
symptom mentions without a question are not."""

_guard_llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
_medical_guard = _guard_llm.with_structured_output(MedicalVerdict)


def check_medical(text: str) -> MedicalVerdict:
    return _medical_guard.invoke(
        [
            {"role": "system", "content": MEDICAL_GUARD_PROMPT},
            {"role": "user", "content": text},
        ]
    )


ADVICE_REDIRECT_MESSAGE = (
    "That's a good one for your care team, not me — I can't give medical advice. "
    "Want me to add it to your list for them?"
)

SELF_DIAGNOSIS_REDIRECT_MESSAGE = (
    "I hear you're worried about that. I'm not the right one to say what it is, "
    "though — that's worth a call to your doctor or care team. Want me to help you "
    "make a note to ask them?"
)


def run_llm_input_rails(text: str) -> RailDecision:
    verdict = check_medical(text)
    if verdict.is_emergency:
        return RailDecision("escalate", "emergency-llm", verdict.reason, EMERGENCY_MESSAGE)
    if verdict.seeking_medical_advice:
        return RailDecision("redirect", "medical-advice", verdict.reason, ADVICE_REDIRECT_MESSAGE)
    if verdict.self_diagnosing:
        return RailDecision(
            "redirect", "self-diagnosis", verdict.reason, SELF_DIAGNOSIS_REDIRECT_MESSAGE
        )
    return RailDecision("allow", "none", "passed", "")


def run_input_rails(text: str) -> RailDecision:
    if decision := run_deterministic_input_rails(text):
        return decision
    return run_llm_input_rails(text)


@before_model(can_jump_to=["end"])
def input_rails_middleware(state: AgentState, runtime: Runtime) -> dict | None:
    last_message = state["messages"][-1]
    if last_message.type != "human":
        return None  # mid-loop tool traffic; this turn's input was already checked

    decision = run_input_rails(str(last_message.content))
    if decision.action in ("escalate", "redirect"):
        event_type = (
            EventType.GUARDRAIL_ESCALATED if decision.action == "escalate" else EventType.GUARDRAIL_REDIRECTED
        )
        log_event(
            runtime.store,
            runtime.context.care_team_id,
            event_type.value,
            f"{decision.rail}: {decision.reason}",
            is_concern=(decision.action == "escalate"),
        )
        return {"messages": [AIMessage(decision.message)], "jump_to": "end"}
    return None


# --- Output rails: catch advice that slipped into the model's own draft ---

MEDICAL_AUTHORITY_PATTERNS = [
    r"\bdiagnos(is|e|ed|ing)\b",
    r"\byou\s+(have|might\s+have|probably\s+have)\b.{0,20}\b(disease|condition|infection|syndrome)\b",
    r"\bprescri(be|bed|ption)\b",
    r"\b(increase|decrease|double|stop\s+taking|adjust)\b.{0,20}\b(your\s+)?(dose|dosage)\b",
    r"\b\d+(\.\d+)?\s?(mg|ml|mcg|units?)\b",
]

OUTPUT_FALLBACK_MESSAGE = (
    "I want to be careful here — that's really a question for your doctor or care "
    "team, not me. Want me to help you note it down for them?"
)


def run_output_rails(draft: str) -> tuple[str, list[str]]:
    """Return (final_text, actions). A flagged match means: replace, don't repair."""
    if pattern := first_match(MEDICAL_AUTHORITY_PATTERNS, draft):
        return OUTPUT_FALLBACK_MESSAGE, [f"flagged: medical-authority language {pattern!r}"]

    text, n_found = redact_pii(draft)
    if n_found:
        return text, [f"repaired: redacted {n_found} PII value(s)"]

    return draft, []


@after_model
def output_rails_middleware(state: AgentState, runtime: Runtime) -> dict | None:
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or last_message.tool_calls:
        return None  # a tool call, not a draft reply

    final_text, actions = run_output_rails(str(last_message.content))
    if actions:
        log_event(
            runtime.store,
            runtime.context.care_team_id,
            EventType.GUARDRAIL_OUTPUT_REPAIRED.value,
            "; ".join(actions),
        )
        return {"messages": [AIMessage(content=final_text, id=last_message.id)]}
    return None
