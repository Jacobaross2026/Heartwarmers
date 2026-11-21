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
    real = [f for f in story["footage"] if f.get("real")]
    stock = [f for f in story["footage"] if not f.get("real")]
    seen = set()

    def credit_lines(items):
        out = []
        for f in items:
            key = f.get("url") or f.get("file")
            if key in seen:
                continue
            seen.add(key)
            who = f.get("creator") or f.get("source", "")
            where = f" on {f['platform']}" if f.get("platform") and f.get("platform") != who else ""
            lic = f" ({f['license']})" if f.get("license") and not f.get("real") else ""
            url = f" {f['url']}" if f.get("url") else ""
            out.append(f"• {who}{where}{lic}{url}")
        return out

    if real:
        lines.append("Original footage & photos:")
        lines += credit_lines(real)
    if stock:
        lines.append("Footage:" if not real else "Additional footage:")
        lines += credit_lines(stock)
    if music.get("source") and music.get("file") != "generated":
        lines.append(f"Music: {music['source']} ({music.get('license', '')})")
    lines += ["", "Voiceover, captions and editing: Warm Hearts Daily",
              "", "#kindness #heartwarming #shorts #goodnews #wholesome"]
    return "\n".join(lines)
