"""Bring stories from your Grok bots into the studio.

    python -m pipeline.import_story            # check + prepare everything in stories/inbox/
    python -m pipeline.import_story --make     # ...and render each one straight away

For each file in stories/inbox/ (Grok's answer, pasted as-is):
  1. find the { ... } block and read it
  2. check it in plain English (word count, hooks, titles, sources, shots)
  3. pick Pixabay stock footage for each shot (records creator, link, license)
  4. pick a title whose style wasn't used in the last 2 videos
  5. save stories/<id>.json and move the original to stories/inbox/done/
"""
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from .config import ASSETS, STORIES
from .qc import last_title_styles

INBOX = STORIES / "inbox"
MIN_WORDS, MAX_WORDS = 42, 54  # 20-25s at Kristen's pace (54 words measured 24.6s)


class Problem(Exception):
    pass


def extract_json(text: str) -> dict:
    """Grok sometimes adds ```json fences or a sentence before/after. Find the JSON block."""
    text = text.replace("“", '"').replace("”", '"')  # curly quotes from copy-paste
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise Problem("No { ... } block found. Copy Grok's whole answer, including the curly brackets.")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise Problem(f"The JSON block is broken near line {e.lineno} ({e.msg}). "
                      f"Ask Grok to 'answer again with valid JSON only'.")


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "story"


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+", text.strip()) if s]


def check(d: dict) -> tuple[list[str], list[str]]:
    """Returns (problems that block the story, warnings)."""
    errs, warns = [], []
    st, sc = d.get("story", {}), d.get("script", {})
    for k in ("who", "what"):
        if not st.get(k):
            errs.append(f"story.{k} is empty.")
    if not [s for s in st.get("sources", []) if s.get("url")]:
        errs.append("No source link. Every story needs at least one real source to credit.")
    if st.get("celebrity_involved"):
        warns.append("Celebrity story: these underperform on the channel.")

    hooks = sc.get("hooks", [])
    if len(hooks) < 3:
        warns.append(f"Expected 3 hooks, got {len(hooks)}.")
    if not hooks:
        errs.append("No hook.")
    else:
        ch = sc.get("chosen_hook", 0)
        if not 0 <= ch < len(hooks):
            errs.append("chosen_hook points to a hook that doesn't exist.")
        elif hooks[ch].get("style") != "stakes_first":
            warns.append(f"The chosen hook is '{hooks[ch].get('style')}', not stakes-first. "
                         f"Stakes-first hooks perform best.")
    for k in ("body", "question"):
        if not sc.get(k):
            errs.append(f"script.{k} is empty.")
        elif len(hooks[ch].get("text", "").split()) > 10:
            warns.append("The hook is over 10 words; it's the big opening text, so shorter reads better.")

    titles = sc.get("titles", [])
    if len(titles) < 3:
        warns.append(f"Expected 3 titles, got {len(titles)}.")
    if not titles:
        errs.append("No titles.")
    if len({t.get("style") for t in titles}) < len(titles):
        warns.append("Some titles share the same style; they should all be different.")

    if hooks and sc.get("body") and sc.get("question"):
        spoken = f"{hooks[sc.get('chosen_hook', 0)]['text']} {sc['body']} {sc['question']}"
        n = len(spoken.split())
        if n < MIN_WORDS:
            errs.append(f"Script is {n} words; it needs {MIN_WORDS}-{MAX_WORDS} to land at 20-25 seconds. "
                        f"Ask Grok to add a sentence.")
        elif n > MAX_WORDS:
            errs.append(f"Script is {n} words; it needs {MIN_WORDS}-{MAX_WORDS} to land at 20-25 seconds. "
                        f"Ask Grok to cut a sentence.")
        n_sent = len(sentences(spoken))
        n_shots = len(d.get("shots", []))
        if n_shots == 0:
            errs.append("No shots listed. Each spoken sentence needs a footage search.")
        elif n_shots != n_sent:
            warns.append(f"{n_shots} shots for {n_sent} sentences; cuts will be spaced evenly "
                         f"instead of landing on sentence starts.")
    for i, sh in enumerate(d.get("shots", []), 1):
        if not sh.get("search") and not sh.get("file"):
            errs.append(f"Shot {i} has no search words.")
    media = d.get("story_media") or d.get("story_footage") or []
    if not [m for m in media if m.get("url")]:
        warns.append("No story_media links: the video will be all stock footage, which won't pass the "
                     "quality check. Ask Grok for the story's original videos/photos.")
    return errs, warns


def best_match(hits: list[dict], query: str) -> dict:
    """Prefer clips whose tags match the search best. Pixabay lists the most important
    tags first, so early matches count more, and the exact phrase counts most."""
    words = [w.lower().rstrip("s") for w in query.split() if len(w) > 2]
    phrase = query.lower().strip()

    def score(h):
        tags = [t.strip().lower() for t in h["tags"].split(",")]
        total = 3.0 if phrase in tags else 0.0
        for w in words:
            pos = next((i for i, t in enumerate(tags) if w in t), None)
            if pos is not None:
                total += 1 + 1 / (1 + pos)
        return total
    return max(hits, key=lambda h: (score(h), -hits.index(h)))


def stock_for(sh: dict, i: int, used: set) -> dict:
    """One Pixabay clip for a shot, never the same clip twice in a video."""
    from .stock import pixabay
    q = sh.get("search") or "happy people"
    hits = []
    for query in (q, " ".join(q.split()[:2]), q.split()[0]):
        hits = [h for h in pixabay.search(query.replace(" ", "+"), 20)
                if h["id"] not in used and h["duration"] >= 4]
        if hits:
            break
    if not hits:
        raise Problem(f"No Pixabay footage found for shot {i} ('{q}'). Change its search words.")
    h = best_match(hits, q)
    used.add(h["id"])
    rec = pixabay.download(h, f"pixabay-{h['id']}")
    rec.update({"beat": sh.get("sentence", "")[:60], "search": q,
                "start": round(min(1.0, h["duration"] * 0.1), 1), "focus_x": 0.5, "framing": "crop"})
    print(f"   shot {i}: stock '{q}' -> Pixabay {h['id']} by {h['creator']}")
    return rec


def real_slots(shots: list[dict], n_real: int) -> list[int]:
    """Which shots get the story's own footage. Grok's "use": "real" wins; otherwise the
    hook, the payoff (second to last) and the middle, in that order."""
    marked = [i for i, sh in enumerate(shots) if sh.get("use") == "real"]
    if marked:
        return marked[:n_real]
    order = [0, len(shots) - 2, len(shots) // 2, 1, len(shots) - 3, len(shots) - 1]
    slots = []
    for i in order:
        if 0 <= i < len(shots) and i not in slots:
            slots.append(i)
    return slots[:n_real]


def build_footage(shots: list[dict], real: list[dict]) -> list[dict]:
    # photos and the original upload first; one real item per shot
    real = sorted(real, key=lambda r: (not r["is_original"], r["kind"] != "video"))
    slots = real_slots(shots, len(real))
    by_slot = dict(zip(slots, real))  # best media goes to the most important slot
    used, footage = set(), []
    for i, sh in enumerate(shots):
        if sh.get("file"):  # a file you placed yourself
            footage.append(sh)
        elif i in by_slot:
            rec = dict(by_slot[i], beat=sh.get("sentence", "")[:60], search=sh.get("search", ""),
                       start="auto", focus_x="auto", framing="auto")
            print(f"   shot {i + 1}: REAL {Path(rec['file']).name} ({rec['platform']})")
            footage.append(rec)
        else:
            footage.append(stock_for(sh, i + 1, used))
    return footage


def choose_title(titles: list[dict]) -> int:
    recent = last_title_styles(2)
    for i, t in enumerate(titles):
        if t.get("style") not in recent:
            return i
    return 0


def import_file(path: Path) -> Path:
    d = extract_json(path.read_text(encoding="utf-8", errors="replace"))
    errs, warns = check(d)
    for w in warns:
        print(f"   note: {w}")
    if errs:
        raise Problem("\n".join(f"- {e}" for e in errs))

    st, sc = d["story"], d["script"]
    sid = d.get("id") or slugify(f"{st.get('hero_type') or st['who']} {st.get('date') or date.today()}")
    out = STORIES / f"{sid}.json"
    n = 2
    while out.exists():
        out = STORIES / f"{sid}-{n}.json"
        n += 1
    sid = out.stem

    from .source_media import fetch
    media = d.get("story_media") or d.get("story_footage") or []
    real, problems = fetch(media, sid)
    for p in problems:
        print(f"   note: {p}")
    if not real:
        print("   WARNING: no real story footage downloaded; the quality check will block this video.")
    footage = build_footage(d["shots"], real)
    sc["chosen_title"] = choose_title(sc["titles"])
    story = {
        "id": sid,
        "status": "draft",
        "is_sample": bool(d.get("is_sample", False)),
        "imported_from": path.name,
        "story": {**st, "category": st.get("category", "everyday_hero_kindness")},
        "story_media": media,
        "script": sc,
        "footage": footage,
        "music": d.get("music", {"file": "auto", "source": "", "license": ""}),
    }
    out.write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    (ASSETS / "footage").mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in INBOX.iterdir() if p.is_file() and p.suffix.lower() in (".txt", ".json", ".md")
                   and p.name.lower() != "readme.md")
    if not files:
        print(f"The inbox is empty. Save Grok's answer as a .txt file in {INBOX}")
        return 0
    made, failed = [], 0
    for p in files:
        print(f"\n==> {p.name}")
        try:
            out = import_file(p)
        except Problem as e:
            failed += 1
            print(f"   NOT IMPORTED. Fix these and try again:\n{e}")
            continue
        (INBOX / "done").mkdir(exist_ok=True)
        shutil.move(str(p), INBOX / "done" / p.name)
        print(f"   saved {out.relative_to(STORIES.parent)}")
        made.append(out)

    if "--make" in sys.argv:
        from .make_short import main as make
        for out in made:
            print(f"\n######## Making {out.stem}")
            make(str(out))
    print(f"\nDone: {len(made)} imported, {failed} need fixing.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
