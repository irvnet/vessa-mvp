"""The guard that decides whether a proactive check-in fires.

It previously tested `messages[-1].type != "ai"`, which silently disabled the whole
scheduler: a reply to the receiver is an AIMessage too, so after any exchange the last
message was always "ai" and the job skipped forever — proactivity, the product's whole
differentiator, only ever worked on a brand-new thread. These lock the distinction
between a reply and an unanswered proactive push."""

from datetime import timedelta

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.config import now_local
from app.scheduler import (
    FOLLOWUP_AFTER_MINUTES,
    PROACTIVE_AT,
    _should_checkin,
    proactive_message,
)


class _FakeAgent:
    """get_state is the only thing the guard touches."""

    def __init__(self, messages):
        self._messages = messages

    def get_state(self, _config):
        return type("State", (), {"values": {"messages": self._messages}})()


def human():
    return HumanMessage("morning!")


def reply():
    return AIMessage("Good morning, Rose.")


def tool_call():
    return ToolMessage(content="ok", tool_call_id="call-1")


@pytest.mark.parametrize(
    ("name", "messages"),
    [
        ("empty thread", []),
        ("her turn is last", [human()]),
        # The regression: an ordinary exchange must not silence the scheduler.
        ("ordinary exchange", [human(), reply()]),
        ("exchange involving a tool call", [human(), reply(), tool_call(), reply()]),
        ("she answered the check-in", [proactive_message("hi"), human(), reply()]),
    ],
)
def test_check_in_fires(name, messages):
    assert _should_checkin(_FakeAgent(messages), "companion-team-rose"), name


@pytest.mark.parametrize(
    ("name", "messages"),
    [
        ("proactive push still unanswered", [human(), reply(), proactive_message("hi")]),
        ("would be a second push in a row", [proactive_message("hi"), proactive_message("hi")]),
    ],
)
def test_check_in_holds_off(name, messages):
    assert not _should_checkin(_FakeAgent(messages), "companion-team-rose"), name


def _aged_push(minutes_ago: int) -> AIMessage:
    message = proactive_message("hi")
    when = now_local() - timedelta(minutes=minutes_ago)
    message.additional_kwargs[PROACTIVE_AT] = when.isoformat()
    return message


def test_a_stale_unanswered_push_stops_suppressing():
    """Otherwise one ignored nudge silences Vessa forever — and walking on stage with
    a check-in still pending from rehearsal would mean nothing ever fires."""
    assert _should_checkin(_FakeAgent([_aged_push(FOLLOWUP_AFTER_MINUTES + 1)]), "t")
    assert not _should_checkin(_FakeAgent([_aged_push(FOLLOWUP_AFTER_MINUTES - 1)]), "t")


def test_untimestamped_push_is_treated_as_old():
    """Pushes written before timestamping existed shouldn't wedge the scheduler."""
    legacy = AIMessage("hi", additional_kwargs={"proactive_checkin": True})
    assert _should_checkin(_FakeAgent([legacy]), "t")


def test_proactive_messages_are_distinguishable_from_replies():
    assert proactive_message("hi").additional_kwargs.get("proactive_checkin")
    assert not AIMessage("hi").additional_kwargs.get("proactive_checkin")
