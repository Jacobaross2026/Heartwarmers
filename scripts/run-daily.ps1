# Runs the day's Warm Hearts Daily videos. Used by the 8:00 AM scheduled task.
# You can also run it by hand: double-click scripts\make-today.cmd
# Extra options are passed through, e.g.  2026-11-21  or  --reuse-voice
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
New-Item -ItemType Directory -Force "logs" | Out-Null
$log = Join-Path "logs" ("{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))
"===== Run started $(Get-Date) =====" | Out-File -FilePath $log -Append -Encoding utf8
& .venv\Scripts\python.exe -m pipeline.local_daily @args 2>&1 | ForEach-Object { "$_" } |
    Tee-Object -FilePath $log -Append
exit $LASTEXITCODE
