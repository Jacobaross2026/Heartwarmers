"""Make every story in a day's drop folder.

    python -m pipeline.daily drop/2026-11-21

The drop folder mirrors Drive: Warm Hearts Daily/<date>/story-1, story-2, ...
Each story folder holds Grok's script file (the { ... } block) and the story's media files.

For each story: import -> make the Short -> make a review copy small enough for Drive
(under 9.5 MB) -> write upload/<date>/<story>/ with the video, title, description and
quality report. A summary is printed and saved as upload/<date>/summary.txt.
Nothing is published anywhere.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .audio import duration
from .config import OUTPUT, ROOT
from .import_story import Problem, import_file

UPLOAD = ROOT / "upload"
MAX_UPLOAD_MB = 9.5  # Drive uploads from the cloud session are limited to 10 MB


def review_copy(video: Path, out: Path, max_mb: float = MAX_UPLOAD_MB) -> Path:
    """Two-pass H.264 squeezed under max_mb, keeping 1080x1920 and the -14 LUFS audio."""
    size_mb = video.stat().st_size / 1e6
    if size_mb <= max_mb:
        shutil.copyfile(video, out)
        return out
    secs = duration(video)
    audio_kbps = 160
    video_kbps = int((max_mb * 8000 * 0.96) / secs - audio_kbps)
    log = out.with_suffix(".passlog")
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-pix_fmt", "yuv420p",
              "-passlogfile", str(log)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), *common, "-pass", "1", "-an",
                    "-f", "mp4", "/dev/null" if sys.platform != "win32" else "NUL"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), *common, "-pass", "2",
                    "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-movflags", "+faststart", str(out)], check=True)
    for f in log.parent.glob(log.name + "*"):
        f.unlink(missing_ok=True)
    return out


def main(drop: str, out_root: Path | None = None, max_mb: float | None = MAX_UPLOAD_MB,
         reuse_voice: bool = False) -> int:
    """out_root: where finished files go (default upload/<date>). max_mb=None keeps full quality."""
    from .make_short import main as make
    drop_dir = Path(drop)
    date = drop_dir.name
    stories = sorted(p for p in drop_dir.iterdir() if p.is_dir())
    if not stories:
        print(f"No story folders in {drop_dir}. Nothing to make today.")
        return 0
    up_root = Path(out_root) if out_root else UPLOAD / date
    up_root.mkdir(parents=True, exist_ok=True)
    summary, manifest, bad = [f"Warm Hearts Daily - {date}", ""], [], 0

    for folder in stories:
        print(f"\n################ {folder.name}")
        try:
            story_file = import_file(folder, story_id=f"{date}-{folder.name}")
        except Problem as e:
            bad += 1
            summary += [f"{folder.name}: NOT MADE. The script needs fixing:", str(e), ""]
            continue
        except SystemExit as e:
            bad += 1
            summary += [f"{folder.name}: NOT MADE. {e}", ""]
            continue
        sid = story_file.stem
        try:
            code = make(str(story_file), reuse_voice=reuse_voice)
        except (SystemExit, subprocess.CalledProcessError) as e:
            bad += 1
            summary += [f"{folder.name} ({sid}): NOT MADE. {e}", ""]
            continue
        out_dir = OUTPUT / sid
        up = up_root / folder.name
        up.mkdir(parents=True, exist_ok=True)
        status = "READY FOR REVIEW" if code == 0 else "DRAFT, QUALITY CHECK FAILED"
        name = f"{date}_{folder.name}.mp4"
        if max_mb:
            review_copy(out_dir / f"{sid}.mp4", up / name, max_mb)
        else:
            shutil.copyfile(out_dir / f"{sid}.mp4", up / name)
        for txt in ("title.txt", "description.txt", "qc_report.txt"):
            shutil.copyfile(out_dir / txt, up / txt)
        title = (out_dir / "title.txt").read_text(encoding="utf-8").splitlines()[0]
        summary += [f"{folder.name}: {status}", f"  {title}",
                    *[f"  {line}" for line in (out_dir / "qc_report.txt").read_text(encoding="utf-8").splitlines()[1:]
                      if line.strip()], ""]
        manifest.append({"story": folder.name, "id": sid, "status": status,
                         "files": sorted(str(p) for p in up.iterdir())})
        if code != 0:
            bad += 1

    (up_root / "summary.txt").write_text("\n".join(summary), encoding="utf-8")
    (up_root / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print("\n" + "\n".join(summary))
    print(f"Upload folder: {up_root}")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m pipeline.daily drop/<date>")
    sys.exit(main(sys.argv[1], reuse_voice="--reuse-voice" in sys.argv))
