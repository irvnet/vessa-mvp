"""Voice I/O for Vessa — a thin shell around the guarded text agent, nothing more.

Speech-to-text (OpenAI) turns a spoken turn into text that feeds the SAME `/chat`
pipeline, so every guardrail, memory lookup, and deterministic answer still applies —
voice never bypasses the trust layer. Text-to-speech reads Vessa's reply back, behind
a provider switch (`TTS_PROVIDER`) so the voice vendor is a one-line swap: ElevenLabs
for a warm premium voice, OpenAI as a cheaper fallback. No reasoning happens here."""

from __future__ import annotations

import io
import os

import httpx
from openai import OpenAI

from app.config import (
    DEFAULT_VOICE_ID,
    ELEVENLABS_MODEL,
    OPENAI_TTS_INSTRUCTIONS,
    OPENAI_TTS_MODEL,
    OPENAI_TTS_VOICE,
    STT_MODEL,
    load_env,
)

load_env()

_openai = OpenAI()


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Speech → text (OpenAI). The result feeds the normal guarded /chat path."""
    buf = io.BytesIO(audio_bytes)
    buf.name = filename  # the OpenAI client infers the audio format from the name
    result = _openai.audio.transcriptions.create(model=STT_MODEL, file=buf)
    return (result.text or "").strip()


def synthesize(text: str) -> bytes:
    """Text → MP3 audio bytes, via the configured TTS_PROVIDER.

    Default is `openai` — it works on the existing key with no extra plan. Set
    TTS_PROVIDER=elevenlabs for the premium warm voice (needs an ElevenLabs *paid*
    plan — free-tier keys can't use library voices via the API)."""
    provider = os.environ.get("TTS_PROVIDER", "openai").lower()
    if provider == "elevenlabs":
        return _synthesize_elevenlabs(text)
    return _synthesize_openai(text)


def _synthesize_elevenlabs(text: str) -> bytes:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    voice_id = os.environ.get("VESSA_VOICE_ID", DEFAULT_VOICE_ID)
    model = os.environ.get("ELEVENLABS_MODEL", ELEVENLABS_MODEL)  # env swaps realism vs latency
    resp = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": text, "model_id": model},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def _synthesize_openai(text: str) -> bytes:
    resp = _openai.audio.speech.create(
        model=OPENAI_TTS_MODEL,
        voice=OPENAI_TTS_VOICE,
        input=text,
        instructions=OPENAI_TTS_INSTRUCTIONS,  # warm, unhurried delivery
    )
    return resp.content
