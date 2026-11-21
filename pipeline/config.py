"""Shared settings: folder paths and keys from the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

STORIES = ROOT / "stories"
ASSETS = ROOT / "assets"
WORK = ROOT / "work"          # scratch files per video
OUTPUT = ROOT / "output"      # finished drafts for review
STUDIO = ROOT / "studio"      # Remotion project
# Title-style history. Kept in git (state/) so daily cloud runs remember past titles.
HISTORY = ROOT / "state" / "history.json"

# Cloud sessions: use the pre-installed browser for rendering and plain HF downloads.
_CLOUD_BROWSER = Path("/opt/pw-browsers")
if not os.environ.get("REMOTION_BROWSER") and _CLOUD_BROWSER.exists():
    _shells = sorted(_CLOUD_BROWSER.glob("chromium_headless_shell-*/*/chrome-headless-shell"))
    if _shells:
        os.environ["REMOTION_BROWSER"] = str(_shells[-1])
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

FPS = 30
WIDTH, HEIGHT = 1080, 1920

# Timing (seconds)
HOOK_LEAD = 0.25      # tiny pause before the voice starts
END_CARD = 1.2       # seconds the end card holds after the voice finishes

# Quality-check rules
MIN_LEN, MAX_LEN = 20.0, 25.0
TARGET_LUFS = -14.0
LUFS_TOLERANCE = 1.5
OK_RIGHTS = {"owned", "licensed_stock", "permission_granted", "public_domain", "creative_commons"}


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()
