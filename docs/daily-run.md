# Daily run checklist (followed by the 8am scheduled session)

The Grok bot uploads at 7am (Chicago time) to Google Drive:
`Warm Hearts Daily / <YYYY-MM-DD> / story-1, story-2, ...`, each with a script file
(Grok's `{ ... }` block, as .txt/.json or a Google Doc) and the story's media files.

Drive IDs:
- Warm Hearts Daily (Grok's drop folder): `12l8iJ_LkFCZbYgmo5Bq59TEtbRzEc-9o`
- Finished (where drafts go):              `1PEJ4rV3nshMUnpxi6UFqMcf2X4z9zvHW`

Rules: never publish or upload to YouTube. Never edit, move or delete anything in Grok's
date folders. Only add files under **Finished**. If something fails, keep going with the
other stories and say what failed in plain English.

## Steps

1. **Code + tools.** In the repository:
   `git fetch origin claude/zealous-galileo-7xso69 && git checkout claude/zealous-galileo-7xso69`
   then `bash scripts/daily_setup.sh`.
2. **Today's date** in Chicago: `TZ=America/Chicago date +%F` (call it DATE).
3. **Find today's drop.** Google Drive `search_files` with
   `parentId = '12l8iJ_LkFCZbYgmo5Bq59TEtbRzEc-9o' and title = 'DATE'`.
   If there is no such folder (or it has no story folders), stop and report
   "No stories in Drive for DATE".
4. **Download.** List its subfolders (`parentId = '<date folder id>'`), then each subfolder's
   files. Download every file with `download_file_content` (Google Docs export as plain text).
   Copy each saved file to `drop/DATE/<subfolder title>/<file title>`; a Google Doc script
   becomes `script.txt`. If a download fails, note it and continue.
5. **Make the videos.** `.venv/bin/python -m pipeline.daily drop/DATE`
   (non-zero exit only means at least one story failed or didn't pass the quality check;
   still upload what was made).
6. **Upload to Drive.** Create folder `DATE` inside Finished (parentId
   `1PEJ4rV3nshMUnpxi6UFqMcf2X4z9zvHW`), and inside it one folder per story (`story-1`, ...).
   Upload from `upload/DATE/<story>/`:
   - the .mp4: `create_file` with `contentMimeType: video/mp4`,
     `disableConversionToGoogleType: true`, `base64Content` as a file reference
     `sha256:<sha256sum of the file>:<absolute path>` (files are under 10 MB by design);
   - title.txt, description.txt, qc_report.txt: `textContent`, `contentMimeType: text/plain`,
     `disableConversionToGoogleType: true`.
   Upload `upload/DATE/summary.txt` into the `DATE` folder itself.
7. **Remember title styles.** If `state/history.json` changed, commit it
   ("Daily run DATE: title history") and push to `claude/zealous-galileo-7xso69`.
8. **Report.** Finish with the contents of summary.txt and the link to the Finished/DATE folder.
