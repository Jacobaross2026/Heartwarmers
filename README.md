# Warm Hearts Daily – Video Studio

Turns a story file into a finished, branded YouTube Short (1080×1920, 20–25 seconds):
voiceover → word-by-word captions → reframed footage → music that dips under the voice →
branded render → quality check. **Nothing is ever uploaded automatically.** Finished drafts
go into the `output` folder for you to watch and approve.

---

## One-time setup on your Windows laptop

You install four free programs once. Accept the default options in each installer.

1. **Node.js** (runs the video renderer): https://nodejs.org → download the **LTS** version → install.
2. **Python 3.12** (runs the helper steps): https://www.python.org/downloads/ → install.
   On the first installer screen, **tick "Add python.exe to PATH"**.
3. **ffmpeg** (cuts and mixes audio/video): open the Start menu, type **PowerShell**, open it, and paste:
   ```
   winget install Gyan.FFmpeg
   ```
4. **Git** (gets this project onto your laptop): https://git-scm.com/download/win → install.

Close PowerShell and open a fresh one (so it sees the new programs), then paste these lines
one at a time:

```
cd $HOME\Documents
git clone https://github.com/jacobaross2026/heartwarmers.git
cd heartwarmers
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd studio
npm install
cd ..
copy .env.example .env
notepad .env
```

The last line opens your settings file in Notepad. Paste your keys after the `=` signs:
- `ELEVENLABS_API_KEY=` → from elevenlabs.io → your profile → API Keys
- `PIXABAY_API_KEY=` → from pixabay.com/api/docs (shown when you're logged in)

Save and close. The `.env` file is private: it is never uploaded to GitHub.

---

## Make a Short

In PowerShell, inside the `heartwarmers` folder:

```
.venv\Scripts\python -m pipeline.make_short stories\sample-birthday-officers.json
```

It takes a few minutes and prints each step. When it finishes, open
`output\<story-id>\` and you'll find:

| File | What it is |
|---|---|
| `<story-id>.mp4` | the video, ready to watch |
| `title.txt` | the chosen title plus the alternatives |
| `description.txt` | the description, with source and footage credits |
| `qc_report.txt` | the quality check result, in plain English |

**Tip:** if you re-run the same story to tweak visuals, add `--reuse-voice` at the end.
It reuses the existing voiceover so you don't spend ElevenLabs characters.

### The quality check
A video only counts as **ready** if all of these pass. If any fail, it tells you why:
- length is 20–25 seconds
- loudness is about -14 LUFS (YouTube's level)
- captions match the spoken words (≥85%)
- the title style isn't the same one used in either of the last 2 videos
- source and footage credits are in the description
- every clip has a rights status we're allowed to use (`owned`, `licensed_stock`,
  `permission_granted`, `public_domain`, `creative_commons`)
- it isn't a sample/test story

If any clip is marked `"ai_generated": true`, the report reminds you to tick YouTube's
"altered or synthetic content" box when uploading.

---

## Changing the look (one place)

Everything visual lives in **`studio/src/brand.ts`**: colors, font, caption size and position,
hook card, end card text, color grade. Change it there and every future video follows.

To preview the template live in your browser while editing:
```
cd studio
npm run studio
```

## Music
Put soft tracks (piano/strings/acoustic) from the **YouTube Audio Library**
(studio.youtube.com → Audio Library → "No attribution required") into `assets\music\`.
The pipeline picks one per video. If the folder is empty it uses a simple placeholder pad.

## Changing the voice
`ELEVENLABS_VOICE_ID` in `.env` sets the channel voice. Keep it the same for every video so
the channel sounds recognisable. The voice step is swappable (`TTS_PROVIDER`), so another
provider can be added later without touching the rest.

---

## How a story file works

Each story is one JSON file in `stories\`. See `stories\sample-birthday-officers.json`.
- **story**: who, what, where, date, sources (links credited in the description)
- **script**: 3 hooks (the chosen one is stakes-first), the body, a closing question
  for comments, and 3 title options in different styles
- **footage**: one entry per shot, in order. Each entry records the file, where it came from,
  the creator, the license, the **rights status**, whether it's AI-generated, and how to frame
  it (`focus_x`: 0 = keep the left side, 1 = keep the right side; `framing`: `crop` fills the
  screen, `fit` shows the whole picture over a blurred background)

When there is one sentence per shot, cuts land on sentence starts automatically.

## Folder map

```
pipeline/   Python steps: tts/ (voice), captions, footage, audio, stock/ (Pixabay), qc, make_short
studio/     Remotion video template (brand.ts = all brand settings)
stories/    one JSON file per story
assets/     footage/ and music/ (your media; not uploaded to GitHub)
output/     finished drafts for review (not uploaded to GitHub)
work/       temporary files (safe to delete)
```

## What's built so far (Phase 1)
Brand template, voice, captions, footage reframing, music ducking, render, quality check.
**Next:** story finder + scoring, automatic script/title writer, Pixabay auto-search per shot,
optional "upload as Private" with your approval, and the weekly analytics feedback loop.
