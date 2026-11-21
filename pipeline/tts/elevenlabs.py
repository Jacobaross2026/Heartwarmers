"""ElevenLabs voice. Needs ELEVENLABS_API_KEY in .env."""
from pathlib import Path

import requests

from ..config import env

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"


def synthesize(text: str, out_path: Path) -> Path:
    key = env("ELEVENLABS_API_KEY", "proxy-injected")
    voice = env("ELEVENLABS_VOICE_ID", "lXiPxoDwq0d2OK7NdaXw")  # Kristen
    model = env("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    r = requests.post(
        API.format(voice=voice),
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": model,
            # Same settings every video = one consistent channel voice.
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3,
                               "speed": float(env("ELEVENLABS_SPEED", "1.08"))},
        },
        timeout=120,
    )
    if r.status_code != 200:
        raise SystemExit(
            f"ElevenLabs refused the request ({r.status_code}). "
            f"Check ELEVENLABS_API_KEY in .env and your character balance. Details: {r.text[:300]}"
        )
    out_path.write_bytes(r.content)
    return out_path
