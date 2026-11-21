"""Pixabay video search + download. Needs PIXABAY_API_KEY in .env.

Pixabay Content License: free for commercial use, no attribution required
(we credit anyway). Each download is recorded with its page URL and creator.
"""
from pathlib import Path

import requests

from ..config import ASSETS, env

API = "https://pixabay.com/api/videos/"
# AI clips would need an AI disclosure; cartoons/green-screen do not fit the channel.
SKIP_TAGS = ("ai generated", "3d", "cartoon", "greenscreen", "chroma key", "animation")


def search(query: str, per_page: int = 10) -> list[dict]:
    key = env("PIXABAY_API_KEY")
    if not key:
        raise SystemExit("PIXABAY_API_KEY is missing from your .env file.")
    r = requests.get(API, params={"key": key, "q": query, "per_page": per_page,
                                  "safesearch": "true"}, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"Pixabay search failed ({r.status_code}): {r.text[:200]}")
    hits = []
    for h in r.json().get("hits", []):
        tags = h["tags"].lower()
        if any(bad in tags for bad in SKIP_TAGS):
            continue  # skip AI-generated, cartoon and green-screen clips
        v = h["videos"].get("large") or h["videos"].get("medium")
        if not v or not v.get("url"):
            v = h["videos"]["medium"]
        hits.append({
            "id": h["id"], "page": h["pageURL"], "tags": h["tags"], "duration": h["duration"],
            "creator": h["user"], "url": v["url"], "thumb": v.get("thumbnail", ""), "w": v["width"], "h": v["height"],
        })
    return hits


def download(hit: dict, name: str) -> dict:
    """Download a hit into assets/footage and return its footage record for the story JSON."""
    dest = ASSETS / "footage" / f"{name}.mp4"
    if not dest.exists():
        with requests.get(hit["url"], stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    return {
        "file": f"assets/footage/{dest.name}",
        "source": "Pixabay",
        "creator": hit["creator"],
        "url": hit["page"],
        "license": "Pixabay Content License",
        "rights_status": "licensed_stock",
        "ai_generated": False,
    }
