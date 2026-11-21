"""Voice + music bed: music ducks under the voice, final mix normalised to -14 LUFS."""
import json
import random
import re
import subprocess
from pathlib import Path

from .config import ASSETS, TARGET_LUFS


def pick_music(story: dict, work: Path) -> tuple[Path, dict]:
    m = story.get("music", {})
    if m.get("file") and m["file"] != "auto":
        return ASSETS.parent / m["file"], m
    tracks = sorted(p for p in (ASSETS / "music").iterdir() if p.suffix.lower() in (".mp3", ".wav", ".m4a"))
    if tracks:
        t = random.Random(story["id"]).choice(tracks)
        return t, {"file": f"assets/music/{t.name}", "source": "YouTube Audio Library", "license": "check track"}
    return placeholder_pad(work / "pad.wav"), {"file": "generated", "source": "Generated placeholder pad",
                                                "license": "own work"}


def placeholder_pad(out: Path, seconds: float = 40) -> Path:
    """A soft, warm two-chord pad (Cmaj7 -> Am7). Only used when assets/music is empty."""
    def chord(freqs):
        return "+".join(f"sin(2*PI*{f}*t)" for f in freqs)
    c, a = chord([130.81, 164.81, 196.0, 246.94, 329.63]), chord([110.0, 164.81, 196.0, 261.63, 329.63])
    expr = f"0.05*(if(lt(mod(t,8),4),{c},{a}))*(0.8+0.2*sin(2*PI*0.25*t))"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"aevalsrc='{expr}':s=44100:d={seconds}",
                    "-af", "lowpass=f=1800,aecho=0.8:0.7:120|240:0.35|0.25,afade=t=in:d=1.5",
                    "-ac", "2", str(out)], check=True)
    return out


def mix(voice: Path, music: Path, out: Path, lead: float, total: float) -> Path:
    """Voice starts after `lead` seconds; music ducks while the voice speaks."""
    delay = int(lead * 1000)
    graph = (
        f"[0:a]aresample=48000,adelay={delay}|{delay},apad,atrim=0:{total},asplit=2[v][key];"
        f"[1:a]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{total},volume=0.55,"
        f"afade=t=out:st={total-1.5}:d=1.5[m];"
        f"[m][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck];"
        f"[v][duck]amix=inputs=2:normalize=0[mixed]"
    )
    tmp = out.with_suffix(".pre.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice), "-i", str(music),
                    "-filter_complex", graph, "-map", "[mixed]", "-ac", "2", str(tmp)], check=True)
    normalize(tmp, out)
    return out


def normalize(src: Path, out: Path) -> None:
    """Two-pass loudness normalisation to -14 LUFS, peaks under -1 dBTP."""
    target = f"I={TARGET_LUFS}:TP=-1.0:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"loudnorm={target}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    stats = json.loads(re.search(r"\{[^{}]*\}\s*$", r.stderr).group(0))
    af = (f"loudnorm={target}:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
          f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
          f"offset={stats['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", "48000", str(out)],
                   check=True)


def measure_lufs(path: Path) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else float("nan")


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())
