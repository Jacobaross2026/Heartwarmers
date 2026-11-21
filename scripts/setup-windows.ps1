# Warm Hearts Daily studio - one-time setup for Windows.
# Run it from the project folder in PowerShell:
#     powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
# Safe to run again (it skips anything already done).

# "Continue": harmless warnings from installers must not stop the script.
# Real failures are caught by checking each step's exit code below.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Say($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}
function Works($exe, $arg) {
    try { $out = & $exe $arg 2>&1 | Out-String; return ($LASTEXITCODE -eq 0 -and $out.Trim().Length -gt 0) }
    catch { return $false }
}

Say "1/7 Installing Node.js, Python and ffmpeg (skipped if already installed)"
if (-not (Works "node" "--version")) {
    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements; Refresh-Path
} else { Write-Host "   Node.js already installed" }
$py = (& python --version 2>&1 | Out-String)
if (-not ($py -match "Python 3\.1[0-3]")) {
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements; Refresh-Path
} else { Write-Host "   $($py.Trim()) already installed" }
if (-not (Works "ffmpeg" "-version")) {
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements; Refresh-Path
} else { Write-Host "   ffmpeg already installed" }

Say "2/7 Python helpers (voice, captions, footage tools)"
if (-not (Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Python didn't install correctly. Close PowerShell, open a new one and run setup again." }
& .venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) { throw "Installing the Python helpers failed (see the messages above)." }

Say "3/7 Video renderer (Remotion) - this one takes a few minutes"
Push-Location studio
& npm.cmd ci --no-audit --no-fund --loglevel=error
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Installing the video renderer failed (see the messages above)." }
& npx.cmd remotion browser ensure
Pop-Location

Say "4/7 Downloading the caption speech model (one time, about 500 MB)"
$env:PYTHONUTF8 = "1"
& .venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('   speech model ready')"
if ($LASTEXITCODE -ne 0) { throw "Downloading the speech model failed. Check your internet connection and run setup again." }

Say "5/7 Your settings file (.env)"
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
$envText = Get-Content ".env" -Raw
if ($envText -notmatch "(?m)^DRIVE_DROP_DIR=[^\r\n]+") {
    $drive = (& .venv\Scripts\python.exe -c "from pipeline.local_daily import drive_folder; print(drive_folder())" 2>$null | Out-String).Trim()
    if ($drive) {
        if ($envText -match "(?m)^DRIVE_DROP_DIR=[ \t]*\r?$") {
            $lines = Get-Content ".env" | ForEach-Object {
                if ($_ -match "^DRIVE_DROP_DIR=\s*$") { "DRIVE_DROP_DIR=$drive" } else { $_ }
            }
            [IO.File]::WriteAllLines((Join-Path $Root ".env"), $lines)
        } else { Add-Content ".env" "`nDRIVE_DROP_DIR=$drive" }
        Write-Host "   Found your synced Drive folder: $drive"
    } else {
        Write-Host "   Couldn't find 'Warm Hearts Daily' in Google Drive for desktop." -ForegroundColor Yellow
        Write-Host "   Add a line DRIVE_DROP_DIR=<full path to that folder> in .env (Notepad opens next)." -ForegroundColor Yellow
    }
}
Write-Host "   Notepad is opening .env. Paste your ElevenLabs and Pixabay keys after the = signs,"
Write-Host "   then SAVE and CLOSE Notepad to continue."
Start-Process notepad.exe ".env" -Wait

Say "6/7 Scheduling the daily run at 8:00 AM"
$runner = Join-Path $Root "scripts\run-daily.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File `"$runner`""
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00am
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -RunOnlyIfNetworkAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 3)
Register-ScheduledTask -TaskName "Warm Hearts Daily" -Action $action -Trigger $trigger -Settings $settings `
    -Description "Makes the day's Warm Hearts Daily Shorts from the Drive drop folder. Never publishes." -Force | Out-Null
Write-Host "   Task 'Warm Hearts Daily' runs every day at 8:00 AM (wakes the laptop from sleep;"
Write-Host "   if the laptop was off, it runs as soon as you're back)."

Say "7/7 Allowing the laptop to wake up for it"
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1 | Out-Null
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1 | Out-Null
powercfg /SETACTIVE SCHEME_CURRENT | Out-Null
Write-Host "   Wake timers turned on for your current power plan."

Write-Host "`nAll set!" -ForegroundColor Green
Write-Host "To make today's videos right now, double-click scripts\make-today.cmd"
Write-Host "Finished videos go to: $HOME\Videos\Warm Hearts Daily (change VIDEOS_DIR in .env to move them)"
