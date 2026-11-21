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

## Feed stories from your Grok bots

Your Grok bots keep finding stories and writing scripts; the studio does the rest.
Full steps and the instructions block to paste into Grok: **`docs\grok-instructions.md`**.

1. Grok answers in a fixed format (one `{ ... }` block).
2. Save the answer as a `.txt` file in `stories\inbox\`.
3. Run:
   ```
   .venv\Scripts\python -m pipeline.import_story --make
   ```
   It checks the story (length, hooks, titles, sources), **downloads the story's own videos
   and photos** from the links Grok gave (`story_media`), places them on the key moments
   (hook and payoff first), fills the other sentences with Pixabay stock, chooses a title
   style you haven't used in the last 2 videos, then renders.
   If something's missing, it says what in plain English and leaves the file in the inbox.

An example answer is in `docs\example-grok-answer.txt`.

### The story's own footage (real clips and photos)
- Anything Grok links is treated as cleared to use: **you handle permission yourself**,
  outside the studio. The studio still credits every item on screen ("Video: Smith family")
  and in the description.
- For each real video it picks the steadiest, sharpest few seconds automatically and centres
  the vertical crop on people's faces. Photos with no clear faces are shown whole over a soft
  blurred background.
- Some sites block automatic downloads (often Facebook, Instagram, TikTok, and news sites
  with "are you a robot" checks). The importer tells you which link failed. Either set
  `YTDLP_COOKIES_BROWSER=chrome` (or edge/firefox) in `.env` so it can use your own login,
  or save the file yourself into `assets\footage\<story-id>\` as `real-5.mp4` / `real-6.jpg`
  and add it to the story file.
- A Short with **no** real story footage fails the quality check: all-stock Shorts don't
  get pushed by YouTube.

## Daily automatic run on your laptop (8:00 AM)

Every morning the Grok bot uploads two stories to Google Drive (`Warm Hearts Daily\<date>\story-1`,
`story-2`: a `script.txt` plus the story's videos/photos). Google Drive for desktop syncs them to
your laptop, and at **8:00 AM** a Windows scheduled task makes both videos.

**Finished videos:** `Videos\Warm Hearts Daily\<date>\story-1\` on your laptop (video, title,
description, quality report) plus `summary.txt` for the day. A copy also goes to Drive's
`Warm Hearts Daily\Finished` folder. Nothing is ever published.

**One-time setup** (after the clone steps above, in PowerShell inside the `heartwarmers` folder):
```
git checkout claude/zealous-galileo-7xso69
powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
```
It installs everything, finds your synced Drive folder, opens `.env` for your keys, and creates
the 8:00 AM task. In Google Drive for desktop, right-click `Warm Hearts Daily` and choose
**Available offline** so files are on the laptop before 8:00.

**Good to know**
- The laptop must be on or asleep (not shut down). If it was off at 8:00, the run starts as soon
  as you're back. It waits up to an hour for Grok's upload to finish syncing.
- **Make videos now:** double-click `scripts\make-today.cmd`.
- **Redo a day without spending voice characters:** in PowerShell,
  `scripts\run-daily.ps1 2026-11-21 --reuse-voice` (delete that day's story folder in
  `Videos\Warm Hearts Daily` first, since finished stories are skipped).
- Each run writes a log to `logs\<date>.log`.
- Change the time: open Task Scheduler, find "Warm Hearts Daily", edit the trigger.

## Make a Short from a story file

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
- at least one shot is the story's own footage or photo
- every clip has a rights status filled in (stock is recorded automatically; story media
  is marked as cleared because you handle permission yourself)
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
The channel voice is **Kristen** (ElevenLabs), read at speed 1.08 (`ELEVENLABS_SPEED`).
At that pace, 45–52 spoken words make a 20–25 second Short.
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
pipeline/   Python steps: tts/ (voice), captions, footage, audio, stock/ (Pixabay), qc,
            make_short, import_story (Grok inbox)
docs/       Grok instructions + example answer
studio/     Remotion video template (brand.ts = all brand settings)
stories/    one JSON file per story
assets/     footage/ and music/ (your media; not uploaded to GitHub)
output/     finished drafts for review (not uploaded to GitHub)
work/       temporary files (safe to delete)
```

## What's built so far (Phase 1)
Brand template, voice, captions, footage reframing, music ducking, render, quality check.
Grok import with automatic Pixabay footage per sentence.
**Next:** story scoring, automatic script/title writer,
optional "upload as Private" with your approval, and the weekly analytics feedback loop.
