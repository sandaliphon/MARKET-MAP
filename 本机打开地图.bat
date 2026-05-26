@echo off
setlocal
cd /d "%~dp0"

set "PORT=8765"
set "URL=http://127.0.0.1:%PORT%/index.html"

echo Starting local map server...
echo URL: %URL%
echo.
echo Keep this window open while viewing the maps.
echo Press Ctrl+C in this window to stop the server.
echo.

start "" "%URL%"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m http.server %PORT% --bind 127.0.0.1 --directory output
) else (
    python -m http.server %PORT% --bind 127.0.0.1 --directory output
)

endlocal
