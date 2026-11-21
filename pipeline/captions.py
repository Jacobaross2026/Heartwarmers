"""Word-level timestamps from the voiceover, for word-by-word captions."""
import json
import re
from pathlib import Path

from .config import env

_last_heard: list[dict] = []


def transcribe_words(audio: Path, script_text: str) -> list[dict]:
    from faster_whisper import WhisperModel

    # CPU is plenty fast for a 25-second clip and avoids GPU driver setup on Windows.
    model = WhisperModel(env("WHISPER_MODEL", "small"), device=env("WHISPER_DEVICE", "cpu"), compute_type="int8")
    segments, _ = model.transcribe(
        str(audio), word_timestamps=True, language="en", initial_prompt=script_text
    )
    heard = [
        {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
        for seg in segments for w in seg.words if w.word.strip()
    ]
    global _last_heard
    _last_heard = heard  # what Whisper actually heard, used by the quality check
    return align_to_script(heard, script_text)


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align_to_script(heard: list[dict], script_text: str) -> list[dict]:
    """Show the script's exact spelling on screen, using Whisper's timing.

    Whisper may write "8" for "Eight" or split a word; matching words copy
    Whisper's timing, and any unmatched script words are spaced evenly
    between their matched neighbours.
    """
    import difflib
    script_words = script_text.split()
    a = [_norm(w) for w in script_words]
    b = [_norm(h["word"]) for h in heard]
    times: list = [None] * len(script_words)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            h = heard[blk.b + k]
            times[blk.a + k] = (h["start"], h["end"])
    # fill gaps by interpolation
    end_all = heard[-1]["end"] if heard else 0.0
    i = 0
    while i < len(times):
        if times[i] is None:
            j = i
            while j < len(times) and times[j] is None:
                j += 1
            t0 = times[i - 1][1] if i > 0 else 0.0
            t1 = times[j][0] if j < len(times) else end_all
            step = max(t1 - t0, 0.05 * (j - i)) / (j - i)
            for k in range(i, j):
                times[k] = (t0 + (k - i) * step, t0 + (k - i + 1) * step)
            i = j
        i += 1
    return [{"word": w, "start": round(t[0], 3), "end": round(t[1], 3)} for w, t in zip(script_words, times)]


def match_score(heard_text: str, script_text: str) -> float:
    """Share of script words that Whisper actually heard (0..1)."""
    import difflib
    a = [_norm(w) for w in script_text.split() if _norm(w)]
    b = [_norm(w) for w in heard_text.split() if _norm(w)]
    return difflib.SequenceMatcher(None, a, b).ratio()


def save(words: list[dict], path: Path) -> None:
    path.write_text(json.dumps(words, indent=1))
