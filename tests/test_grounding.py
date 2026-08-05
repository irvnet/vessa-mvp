"""The time/day path is the one place Vessa refuses to let the model answer at all.
These lock in the two halves of that: the question is recognised, and the answer built
in Python is right — including the AM/PM split that gpt-4o-mini was observed getting
wrong with the correct timestamp sitting in its prompt."""

from datetime import datetime

import pytest

from app.agent import deterministic_time_answer, is_time_or_date_question


@pytest.mark.parametrize(
    "question",
    [
        "What time is it?",
        "what's the time",
        "Do you know what time it is?",
        "Have you got the time?",
        "Can you tell me the time please",
        "What day is it?",
        "what day of the week is it",
        "What's today's date?",
    ],
)
def test_recognises_every_time_or_date_phrasing(question):
    assert is_time_or_date_question(question)


@pytest.mark.parametrize(
    "message",
    [
        "How's Biscuit doing today?",
        "Tell me about my rose garden",
        "I had a lovely time yesterday",  # 'time' present, but not a time question
    ],
)
def test_ordinary_conversation_is_left_to_the_model(message):
    assert not is_time_or_date_question(message)


@pytest.mark.parametrize(
    ("hour", "expected"),
    [
        (3, "in the morning"),
        (9, "in the morning"),
        (15, "in the afternoon"),
        (19, "in the evening"),
        (22, "at night"),
    ],
)
def test_hour_maps_to_the_right_part_of_day(hour, expected):
    """The AM/PM regression: 15:20 must never read as 3:20 in the morning."""
    answer = deterministic_time_answer("Rose", datetime(2026, 8, 6, hour, 20))
    assert "3:20" in answer or f"{hour % 12 or 12}:20" in answer
    assert expected in answer


def test_answer_carries_day_and_date_not_just_the_clock():
    """Both are always included — the extra grounding is the point, not clutter."""
    answer = deterministic_time_answer("Rose", datetime(2026, 8, 6, 15, 20))
    assert "Rose" in answer
    assert "Thursday" in answer
    assert "August 6" in answer


def test_on_the_hour_reads_as_spoken_not_zero_padded():
    answer = deterministic_time_answer("Rose", datetime(2026, 8, 6, 14, 0))
    assert "2 o'clock in the afternoon" in answer
    assert "2:00" not in answer
