"""Reframe each shot to 9:16 (1080x1920) and cut it to length.

framing = "crop": fill the frame, centred on focus_x (0 = left edge, 1 = right).
framing = "fit":  whole picture visible, with a soft blurred copy filling the gaps.
"""
import subprocess
from pathlib import Path

from .config import FPS, HEIGHT, ROOT, WIDTH


def _probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


def resolve_auto(shot: dict, duration: float) -> dict:
    """Fill in "auto" start / focus / framing for real footage and photos."""
    from . import analyze
    src = ROOT / shot["file"]
    is_img = src.suffix.lower() in IMAGE_EXT
    shot = dict(shot)
    if shot.get("start", "auto") == "auto":
        shot["start"] = 0.0 if is_img else analyze.best_start(src, duration)
    if shot.get("focus_x", "auto") == "auto":
        shot["focus_x"] = analyze.face_focus(src, float(shot["start"]), duration, image=is_img)
    if shot.get("framing", "auto") == "auto":
        a = analyze.aspect(src, image=is_img)
        found_face = shot["focus_x"] != 0.5
        # tall media fills the screen; wide media is cropped only when we know where the people are
        shot["framing"] = "crop" if a <= 0.8 or (found_face and a <= 1.9) else "fit"
    return shot


def prepare_shot(shot: dict, duration: float, out: Path) -> Path:
    src = ROOT / shot["file"]
    if not src.exists():
        raise SystemExit(f"Footage file not found: {shot['file']}. Put it in assets/footage/.")
    shot = resolve_auto(shot, duration)
    is_img = src.suffix.lower() in IMAGE_EXT
    start = float(shot.get("start", 0))
    fx = float(shot.get("focus_x", 0.5))
    if is_img:
        stretch, inp = 1.0, ["-loop", "1", "-framerate", str(FPS), "-i", str(src)]
    else:
        avail = _probe_duration(src) - start
        # If the clip is too short, slow it down gently (max 1.5x) instead of freezing.
        stretch = max(1.0, min(1.5, duration / max(avail, 0.1)))
        inp = ["-ss", str(start), "-i", str(src)]
    if shot.get("framing", "crop") == "fit":
        vf = (f"split[a][b];[a]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
              f"crop={WIDTH}:{HEIGHT},boxblur=30:2,eq=brightness=-0.08[bg];"
              f"[b]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2")
    else:
        vf = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
              f"crop={WIDTH}:{HEIGHT}:'min(max(iw*{fx}-{WIDTH}/2,0),iw-{WIDTH})':'(ih-{HEIGHT})/2'")
    vf += f",setpts={stretch}*PTS,fps={FPS},tpad=stop_mode=clone:stop_duration=2,setsar=1,format=yuv420p"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", *inp,
        "-filter_complex", vf, "-t", f"{duration:.3f}", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out),
    ], check=True)
    return out


def plan_cuts(words: list[dict], n_shots: int, total: float, lead: float) -> list[float]:
    """Shot start times. Cut on sentence starts when there is one sentence per shot,
    otherwise spread evenly. Returns n_shots start times (first is 0)."""
    sentence_starts = [lead + words[0]["start"]]
    for prev, w in zip(words, words[1:]):
        if prev["word"].rstrip('"\'').endswith((".", "?", "!")):
            sentence_starts.append(lead + w["start"] - 0.15)
    if len(sentence_starts) == n_shots:
        starts = [0.0] + sentence_starts[1:]
    else:
        starts = [i * total / n_shots for i in range(n_shots)]
    return starts
