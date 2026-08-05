"""The mention check behind reminder_nudge_middleware. Its job is to decide whether the
model already said the thing; getting it wrong in the permissive direction is what
silently drops a medication reminder, so the bias is deliberately toward nudging."""

import pytest

from app.agent import _mentions_subject


@pytest.mark.parametrize(
    ("reply", "subject"),
    [
        ("Did you get a chance to water the rose garden?", "Water the rose garden"),
        ("Have you taken your morning vitamins?", "Take morning vitamins"),
        ("Time for your heart medication soon.", "Afternoon heart medication"),
        ("Did you call Linda?", "Call Linda back this evening"),
    ],
)
def test_recognises_the_model_paraphrasing_the_reminder(reply, subject):
    assert _mentions_subject(reply, subject)


@pytest.mark.parametrize(
    ("reply", "subject"),
    [
        # The trap: her rose garden is a hobby in the profile, so it comes up in
        # ordinary chat. One shared word must not count as "already reminded".
        ("Have you had a chance to enjoy your rose garden yet?", "Water the rose garden"),
        ("How's your heart been feeling?", "Afternoon heart medication"),
        ("It's a lovely day, isn't it?", "Take morning vitamins"),
    ],
)
def test_incidental_overlap_does_not_count_as_surfaced(reply, subject):
    assert not _mentions_subject(reply, subject)
