import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent

# Rose's real-world timezone (Jersey City, NJ) — hardcoded alongside the
# single hardcoded receiver elsewhere (DEFAULT_CONTEXT, SAMPLE_PROFILE).
_RECEIVER_TZ = ZoneInfo("America/New_York")


def now_local() -> datetime:
    """The receiver's actual local wall-clock time — NOT the deployment
    server's system time. A bare datetime.now() returns whatever timezone
    the server itself is configured for (this project's EC2 instance runs
    UTC, the AWS/Ubuntu default), which silently broke every time-grounding
    claim once deployed, despite working correctly in local dev on an
    Eastern-configured machine. Returned naive (no tzinfo) so it stays
    directly comparable to due_at values, which come from the frontend's
    naive datetime-local inputs (also implicitly Eastern)."""
    return datetime.now(_RECEIVER_TZ).replace(tzinfo=None)

LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"  # powers episodic memory semantic search (store index + companion_prompt's store.search)

# --- Voice I/O (STT via OpenAI; TTS via a swappable provider — see app/voice.py) ---
# Env-dependent values (TTS_PROVIDER, ELEVENLABS_API_KEY, VESSA_VOICE_ID) are read
# at call time in voice.py, AFTER load_env() — never as module constants here, for
# the same reason get_allowed_origins() is a function (config imports before env loads).
STT_MODEL = "whisper-1"  # most tolerant of browser webm/opus (the newer gpt-4o transcribe models 400 on it)
# Flash = low latency; for MOST-realistic voice set ELEVENLABS_MODEL=eleven_multilingual_v2 (richer, a touch slower).
ELEVENLABS_MODEL = "eleven_flash_v2_5"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs "Rachel" (warm/calm) — override with VESSA_VOICE_ID
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"     # fallback provider
OPENAI_TTS_VOICE = "shimmer"
# gpt-4o-mini-tts honors a free-text delivery instruction — this is the warmth lever.
OPENAI_TTS_INSTRUCTIONS = (
    "Speak warmly and unhurriedly, like a familiar friend visiting an older adult — "
    "gentle, calm, and reassuring. Never rushed, clipped, or clinical."
)

# Real persistence for the live app (app/persistence.py) — scripts/tests keep
# using the in-memory defaults in agent.py, so this only affects bootstrap.py.
SQLITE_DB_PATH = ROOT / "data" / "vessa.db"

# Cached eval-run summaries, read by the /proof page — written by each eval
# script's __main__ block, read instantly (no LLM cost) on page load.
EVAL_RESULTS_PATH = ROOT / "data" / "eval_results.json"


def load_env() -> None:
    """Load .env — supports both `export KEY=val` (notebook) and `KEY=val` (systemd)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ")
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, val.strip().strip('"').strip("'"))


def get_allowed_origins() -> list[str]:
    """A function, not a module-level constant — config.py's body runs before
    load_env() is called (agent.py imports config first, then calls
    load_env()), so a constant here would always read the stale/default env."""
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]
