from dataclasses import dataclass, field


@dataclass
class CareContext:
    """Injected per-call via create_agent's context_schema — identifies whose
    profile/memory namespace this conversation belongs to."""

    care_team_id: str
    receiver_id: str


@dataclass
class CompanionProfile:
    """Static grounding for one care receiver. In-repo sample for now — swap
    get_profile() for a DB lookup once we need more than one receiver."""

    name: str
    age: int
    identity: str
    relationships: str
    life_story: str
    interests: str
    tone: str
    boundaries: str
    resolved_issues: list[str] = field(default_factory=list)


SAMPLE_PROFILE = CompanionProfile(
    name="Rose",
    age=84,
    identity=(
        "Rose lives alone in a one-bedroom apartment in Jersey City. Widowed "
        "6 years. Early-stage dementia — mild memory lapses, still independent "
        "for daily activities."
    ),
    relationships=(
        "Daughter Linda (primary caregiver, lives 20 min away, checks in daily "
        "by phone). Son Mark lives out of state, calls on weekends. Rose's late "
        "husband was named Walt — she brings him up often, sometimes as if he's "
        "still alive; gently acknowledge rather than correct."
    ),
    life_story=(
        "Worked 30 years as a school librarian. Grew up in Bayonne. Proud of "
        "raising two kids mostly on her own after Walt's construction accident "
        "left him disabled for a decade before he passed. Loves telling the "
        "story of meeting Walt at a church dance in 1962."
    ),
    interests=(
        "Big band music and jazz standards, crossword puzzles, her cat Biscuit, "
        "watching game shows in the afternoon, her rose garden on the balcony "
        "(where her name-flower joke comes from — she'll make it unprompted)."
    ),
    tone=(
        "Warm, unhurried, never rushed or clipped. Talk to her like a familiar "
        "visitor, not a device or a nurse. No baby talk, no over-explaining. "
        "Comfortable with silence — don't fill every pause."
    ),
    boundaries=(
        "Never diagnose, dose, or advise on medications or symptoms — surface "
        "known facts and redirect to Linda or a professional. Don't argue about "
        "Walt or correct her memory of him. Don't alarm her about her own memory "
        "lapses. Always allow her to decline a check-in or reminder."
    ),
    resolved_issues=[
        "Worry about leaving the stove on — checked repeatedly in early 2026, "
        "confirmed always off. Considered resolved; don't re-raise unless she "
        "brings it up herself.",
    ],
)


def get_profile(_care_team_id: str) -> CompanionProfile:
    """Single hardcoded profile for now, regardless of care_team_id."""
    return SAMPLE_PROFILE


def format_profile_for_prompt(profile: CompanionProfile) -> str:
    """Render the profile as grounding text for injection into the system prompt."""
    resolved = (
        "\n".join(f"- {issue}" for issue in profile.resolved_issues)
        if profile.resolved_issues
        else "- (none yet)"
    )
    return f"""Companion profile for {profile.name} (age {profile.age}):

Identity: {profile.identity}

Relationships: {profile.relationships}

Life story: {profile.life_story}

Interests: {profile.interests}

Tone to use: {profile.tone}

Boundaries: {profile.boundaries}

Resolved issues (do not reopen unless {profile.name} raises them again):
{resolved}"""
