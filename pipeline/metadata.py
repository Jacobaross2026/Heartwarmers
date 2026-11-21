"""Title + description (with source credits) for a story."""


def chosen_title(story: dict) -> dict:
    s = story["script"]
    return s["titles"][s.get("chosen_title", 0)]


def spoken_script(story: dict) -> str:
    s = story["script"]
    hook = s["hooks"][s.get("chosen_hook", 0)]["text"]
    return f"{hook} {s['body']} {s['question']}"


def description(story: dict, music: dict) -> str:
    st, s = story["story"], story["script"]
    lines = [st["what"], "", s["question"] + " Tell us in the comments 👇", ""]
    lines.append("Story sources:")
    for src in st.get("sources", []):
        lines.append(f"• {src['name']}: {src['url']}")
    lines.append("")
    lines.append("Footage:")
    seen = set()
    for f in story["footage"]:
        key = f.get("url") or f.get("source")
        if key in seen:
            continue
        seen.add(key)
        who = f" by {f['creator']}" if f.get("creator") else ""
        url = f" {f['url']}" if f.get("url") else ""
        lines.append(f"• {f['source']}{who} ({f['license']}){url}")
    if music.get("source") and music.get("file") != "generated":
        lines.append(f"Music: {music['source']} ({music.get('license', '')})")
    lines += ["", "Voiceover, captions and editing: Warm Hearts Daily",
              "", "#kindness #heartwarming #shorts #goodnews #wholesome"]
    return "\n".join(lines)
