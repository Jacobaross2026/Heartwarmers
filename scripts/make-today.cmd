@echo off
rem Double-click to make today's Warm Hearts Daily videos now.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-daily.ps1" %*
echo.
echo Done. Press any key to close this window.
pause >nul
