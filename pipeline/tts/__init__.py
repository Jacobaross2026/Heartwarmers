"""Text-to-speech providers. Pick one with TTS_PROVIDER in .env."""
from pathlib import Path

from ..config import env


def synthesize(text: str, out_path: Path) -> Path:
    provider = env("TTS_PROVIDER", "elevenlabs").lower()
    if provider == "elevenlabs":
        from .elevenlabs import synthesize as fn
    else:
        raise SystemExit(f"Unknown TTS_PROVIDER '{provider}'. Check your .env file.")
    return fn(text, out_path)
