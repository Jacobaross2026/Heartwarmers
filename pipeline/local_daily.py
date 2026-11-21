"""The 8am daily run on your own computer.

    python -m pipeline.local_daily              # today's stories
    python -m pipeline.local_daily 2026-11-21   # a specific day (e.g. to redo one)
    add --reuse-voice to redo a day without spending ElevenLabs characters

1. Finds today's folder in your synced Google Drive:  ...\\Warm Hearts Daily\\<date>\\story-1, story-2
2. Waits (up to WAIT_MINUTES) until Grok's upload has finished syncing.
3. Makes every story's Short at full quality.
4. Saves the video, title, description and quality report to
       VIDEOS_DIR\\<date>\\story-N\\         (your hard drive)
   and, if COPY_TO_DRIVE=yes, also to  Warm Hearts Daily\\Finished\\<date>\\story-N\\
5. Writes summary.txt for the day. Stories that are already finished are skipped,
   so running it twice is safe. Nothing is ever published.
"""
import os
import shutil
import string
import sys
import time
from datetime import date as _date
from pathlib import Path

from .config import ROOT, env

STABLE_SECONDS = 60
SKIP_NAMES = (".tmp", ".crdownload", ".partial", "~$", "desktop.ini")


def drive_folder() -> Path:
    """Where Google Drive for desktop shows the 'Warm Hearts Daily' folder."""
    configured = env("DRIVE_DROP_DIR")
    if configured:
        p = Path(configured).expanduser()
        if p.exists():
            return p
        raise SystemExit(f"DRIVE_DROP_DIR in .env points to {p}, which doesn't exist. "
                         f"Open Google Drive for desktop and check the folder path.")
    candidates = []
    if sys.platform == "win32":
        for letter in string.ascii_uppercase:
            for mine in ("My Drive", "Meine Ablage", "Mi unidad"):
                candidates.append(Path(f"{letter}:/{mine}/Warm Hearts Daily"))
    home = Path.home()
    candidates += [home / "Google Drive" / "My Drive" / "Warm Hearts Daily",
                   home / "My Drive" / "Warm Hearts Daily"]
    for c in candidates:
        try:
            if c.exists():
                return c
        except OSError:
            continue
    raise SystemExit("Couldn't find the 'Warm Hearts Daily' folder from Google Drive for desktop. "
                     "Set DRIVE_DROP_DIR in .env to its full path, e.g. G:\\My Drive\\Warm Hearts Daily")


def _files(folder: Path) -> dict[str, int]:
    out = {}
    for f in folder.rglob("*"):
        if f.is_file() and not any(bad in f.name.lower() for bad in SKIP_NAMES):
            try:
                out[str(f.relative_to(folder))] = f.stat().st_size
            except OSError:
                pass
    return out


def wait_for_sync(day: Path, minutes: int) -> bool:
    """Wait for the date folder to appear and its files to stop changing."""
    deadline = time.time() + minutes * 60
    while not day.exists():
        if time.time() > deadline:
            return False
        print(f"   waiting for {day.name} to appear in Drive...", flush=True)
        time.sleep(60)
    last, stable_since = None, time.time()
    while True:
        now = _files(day)
        if now != last:
            last, stable_since = now, time.time()
        elif now and time.time() - stable_since >= STABLE_SECONDS:
            return True
        if time.time() > deadline:
            return bool(now)
        time.sleep(10)


def _finished(dest: Path) -> bool:
    return dest.exists() and any(dest.glob("*.mp4"))


def main(args: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):  # titles have emojis; keep Windows logs happy
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    day_name = next((a for a in args if not a.startswith("--")), _date.today().isoformat())
    reuse = "--reuse-voice" in args
    drive = drive_folder()
    videos = Path(env("VIDEOS_DIR") or Path.home() / "Videos" / "Warm Hearts Daily").expanduser() / day_name
    copy_to_drive = env("COPY_TO_DRIVE", "yes").lower() in ("yes", "y", "true", "1")
    finished_drive = drive / "Finished" / day_name

    print(f"Warm Hearts Daily - {day_name}")
    print(f"   Drive folder: {drive}")
    day = drive / day_name
    if not wait_for_sync(day, int(env("WAIT_MINUTES", "60"))):
        msg = f"No stories in Drive for {day_name} (looked in {day})."
        print(msg)
        videos.mkdir(parents=True, exist_ok=True)
        (videos / "summary.txt").write_text(msg, encoding="utf-8")
        return 0

    # Work on a local copy so Drive syncing can't change files mid-render.
    drop = ROOT / "drop" / day_name
    if drop.exists():
        shutil.rmtree(drop)
    todo = []
    for story in sorted(p for p in day.iterdir() if p.is_dir()):
        if _finished(videos / story.name):
            print(f"   {story.name}: already finished, skipping")
            continue
        shutil.copytree(story, drop / story.name,
                        ignore=shutil.ignore_patterns(*[f"*{s}*" for s in SKIP_NAMES]))
        todo.append(story.name)
    if not todo:
        print("Nothing new to make today.")
        return 0

    from .daily import main as make_day
    out = ROOT / "upload" / day_name
    if out.exists():
        shutil.rmtree(out)
    code = make_day(str(drop), out_root=out, max_mb=None, reuse_voice=reuse)

    targets = [videos] + ([finished_drive] if copy_to_drive else [])
    for target in targets:
        for story in todo:
            src = out / story
            if src.exists():
                shutil.copytree(src, target / story, dirs_exist_ok=True)
        if (out / "summary.txt").exists():
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(out / "summary.txt", target / "summary.txt")
    print(f"\nSaved to: {videos}")
    if copy_to_drive:
        print(f"Also copied to Drive: {finished_drive}")
    if sys.platform == "win32" and env("OPEN_FOLDER_WHEN_DONE", "yes").lower() in ("yes", "y", "true", "1"):
        os.startfile(videos)  # noqa: S606  (opens the folder in Explorer)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
