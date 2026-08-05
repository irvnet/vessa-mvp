"""Confirmation detection behind reminder_acknowledgment_middleware.

The loop used to depend on the model choosing to call acknowledge_reminder, and it was
observed not calling it: Vessa asked whether Rose had watered the garden, Rose said "I
did! I watered them this morning", and the reminder stayed at 'delivered' — so the
caregiver never saw the confirmation. People confirm with pronouns, which is why this
matches on how confirmation *sounds* rather than on the reminder's own words."""

import pytest

from app.agent import _CONFIRMATION_RE


@pytest.mark.parametrize(
    "message",
    [
        "I did! I watered them this morning. Oh, it's fantastic.",
        "Yes, all done.",
        "I already took them, thank you for asking.",
        "just finished, actually",
        "Yep, took my pills after breakfast.",
        "Did it right after we spoke.",
        "mmhm, that's taken care of",
    ],
)
def test_hears_a_confirmation(message):
    assert _CONFIRMATION_RE.search(message)


@pytest.mark.parametrize(
    "message",
    [
        "It's a lovely day out there.",
        "I've just been pottering about this morning.",  # 'just', but nothing confirmed
        "Do you think I should water them today?",
        "I'm not sure I remembered.",
        "Biscuit still isn't eating much.",
    ],
)
def test_does_not_hear_confirmation_in_ordinary_talk(message):
    assert not _CONFIRMATION_RE.search(message)
