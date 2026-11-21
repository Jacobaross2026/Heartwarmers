"""Quality check. Every rule must pass before a video counts as ready.
Failures are written in plain English so you know exactly what to fix."""
import json
import subprocess
from pathlib import Path

from .audio import duration, measure_lufs
from .config import HEIGHT, HISTORY, LUFS_TOLERANCE, MAX_LEN, MIN_LEN, OK_RIGHTS, TARGET_LUFS, WIDTH
from .metadata import chosen_title


def last_title_styles(n: int = 2) -> list[str]:
    if not HISTORY.exists():
        return []
    return [h["title_style"] for h in json.loads(HISTORY.read_text())[-n:]]


def run(video: Path, story: dict, desc: str, caption_match: float) -> tuple[list[str], list[str]]:
    fails, warns = [], []

    length = duration(video)
    if not MIN_LEN <= length <= MAX_LEN:
        fails.append(f"Length is {length:.1f}s; it must be between {MIN_LEN:.0f} and {MAX_LEN:.0f} seconds. "
                     f"Shorten or lengthen the script.")

    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True).stdout.strip().strip(",")
    if probe != f"{WIDTH},{HEIGHT}":
        fails.append(f"Video size is {probe}, expected {WIDTH}x{HEIGHT} (vertical).")

    lufs = measure_lufs(video)
    if not abs(lufs - TARGET_LUFS) <= LUFS_TOLERANCE:
        fails.append(f"Loudness is {lufs:.1f} LUFS; it should be about {TARGET_LUFS:.0f} LUFS.")

    if caption_match < 0.85:
        fails.append(f"Captions don't match the speech well enough ({caption_match:.0%} match, need 85%). "
                     f"The voice may have mispronounced or skipped words; listen and regenerate.")

    style = chosen_title(story)["style"]
    if style in last_title_styles(2):
        fails.append(f"Title style '{style}' was already used in one of the last 2 videos. "
                     f"Pick a different title option.")

    real = [f for f in story["footage"] if f.get("real")]
    if not real:
        fails.append("No real footage or photos from the story itself: all-stock Shorts don't get "
                     "pushed by YouTube. Add the story's own videos/photos (story_media in Grok's answer).")
    elif len(story["footage"]) - len(real) > len(story["footage"]) * 0.6:
        warns.append(f"Only {len(real)} of {len(story['footage'])} shots are real story footage; "
                     f"more real shots usually perform better.")

    if "ootage" not in desc or not story["story"].get("sources"):
        fails.append("Source credits are missing from the description.")

    for f in story["footage"]:
        rs = f.get("rights_status", "")
        if not rs:
            fails.append(f"Rights status is empty for {f.get('file')}. Record where it came from.")
        elif rs not in OK_RIGHTS:
            fails.append(f"Clip {f.get('file')} has rights status '{rs}': we don't have permission to use it yet.")
        if f.get("ai_generated"):
            warns.append(f"{f.get('file')} is AI-generated: tick 'Altered or synthetic content' when uploading.")

    if story.get("is_sample"):
        fails.append("This is a SAMPLE test story, not a real sourced story. Not for publishing.")

    return fails, warns
