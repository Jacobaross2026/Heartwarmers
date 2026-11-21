"""Make one Short from a story JSON, start to finish.

    python -m pipeline.make_short stories/<story>.json

Steps: voiceover -> captions -> footage -> music mix -> render -> quality check -> output/.
Nothing is uploaded anywhere. Finished drafts land in output/<story-id>/ for you to review.
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import audio, captions, footage, metadata, qc, tts
from .config import END_CARD, FPS, HISTORY, HOOK_LEAD, OUTPUT, ROOT, STUDIO, WORK, env


def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def main(story_path: str, reuse_voice: bool = False) -> int:
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    sid = story["id"]
    work = WORK / sid
    work.mkdir(parents=True, exist_ok=True)
    script = metadata.spoken_script(story)

    step("1/6 Voiceover")
    voice = work / "voice.mp3"
    if reuse_voice and voice.exists():
        print("   reusing existing voice.mp3 (saves ElevenLabs characters)")
    else:
        tts.synthesize(script, voice)
    voice_len = audio.duration(voice)
    total = HOOK_LEAD + voice_len + END_CARD
    print(f"   voice {voice_len:.1f}s -> video {total:.1f}s")

    step("2/6 Captions (word timestamps)")
    from faster_whisper import WhisperModel  # noqa: F401  (fail early if missing)
    words = captions.transcribe_words(voice, script)
    heard = " ".join(w["word"] for w in captions._last_heard)
    match = captions.match_score(heard, script)
    captions.save(words, work / "words.json")
    print(f"   {len(words)} words, caption match {match:.0%}")

    step("3/6 Footage (reframe to 9:16)")
    shots = story["footage"]
    starts = footage.plan_cuts(words, len(shots), total, HOOK_LEAD)
    ends = starts[1:] + [total]
    job = STUDIO / "public" / "jobs" / sid
    if job.exists():
        shutil.rmtree(job)
    job.mkdir(parents=True)
    shot_props = []
    for i, (shot, a, b) in enumerate(zip(shots, starts, ends)):
        name = f"shot{i}.mp4"
        footage.prepare_shot(shot, b - a, job / name)
        credit = ""
        if shot.get("real"):
            what = "Photo" if shot.get("kind") == "image" else "Video"
            credit = f"{what}: {shot.get('creator') or shot.get('platform') or shot.get('source')}"
        shot_props.append({"src": f"jobs/{sid}/{name}", "from": round(a * FPS), "dur": round((b - a) * FPS),
                           "credit": credit})
        print(f"   shot {i+1}: {shot.get('beat', shot['file'])} {a:.1f}-{b:.1f}s")
    # make shot lengths add up exactly to the video length in frames
    shot_props[-1]["dur"] = round(total * FPS) - shot_props[-1]["from"]

    step("4/6 Music bed + mix (ducking, -14 LUFS)")
    music_file, music_meta = audio.pick_music(story, work)
    audio.mix(voice, music_file, job / "mix.wav", HOOK_LEAD, total)
    print(f"   music: {music_meta['source']}")

    step("5/6 Render (Remotion, 1080x1920)")
    s = story["script"]
    props = {
        "durationInFrames": round(total * FPS),
        "audio": f"jobs/{sid}/mix.wav",
        "shots": shot_props,
        "words": [{"word": w["word"], "start": w["start"] + HOOK_LEAD, "end": w["end"] + HOOK_LEAD} for w in words],
        "question": s["question"],
        "voiceEnd": HOOK_LEAD + voice_len,
    }
    props_file = work / "props.json"
    props_file.write_text(json.dumps(props))
    out_dir = OUTPUT / sid
    out_dir.mkdir(parents=True, exist_ok=True)
    video = out_dir / f"{sid}.mp4"
    cmd = ["npx", "remotion", "render", "src/index.ts", "Short", str(video), f"--props={props_file}",
           "--codec=h264", "--crf=18", "--audio-codec=aac", "--audio-bitrate=256k"]
    if env("REMOTION_BROWSER"):
        cmd.append(f"--browser-executable={env('REMOTION_BROWSER')}")
    subprocess.run(cmd, cwd=STUDIO, check=True, shell=(sys.platform == "win32"))

    step("6/6 Quality check")
    desc = metadata.description(story, music_meta)
    title = metadata.chosen_title(story)
    fails, warns = qc.run(video, story, desc, match)
    (out_dir / "title.txt").write_text(
        "\n".join([f"CHOSEN: {title['text']}  [{title['style']}]", "", "Other options:"] +
                  [f"- {t['text']}  [{t['style']}]" for t in s["titles"] if t is not title]), encoding="utf-8")
    (out_dir / "description.txt").write_text(desc, encoding="utf-8")
    report = ["QUALITY CHECK: " + ("PASSED" if not fails else "FAILED")]
    report += [f"  FAIL: {f}" for f in fails] + [f"  NOTE: {w}" for w in warns]
    report += ["", f"Length {audio.duration(video):.1f}s | Loudness {audio.measure_lufs(video):.1f} LUFS | "
                   f"Caption match {match:.0%}"]
    (out_dir / "qc_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))

    if fails:
        print(f"\n!! NOT READY. Draft saved for review only: {video}")
        return 1
    hist = json.loads(HISTORY.read_text()) if HISTORY.exists() else []
    hist.append({"id": sid, "title": title["text"], "title_style": title["style"],
                 "made": datetime.now().isoformat(timespec="seconds")})
    HISTORY.write_text(json.dumps(hist, indent=1))
    print(f"\nReady for your review: {video}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit("Usage: python -m pipeline.make_short stories/<story>.json [--reuse-voice]")
    sys.exit(main(args[0], reuse_voice="--reuse-voice" in sys.argv))
