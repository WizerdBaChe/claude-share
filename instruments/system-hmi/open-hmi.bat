@echo off
rem system-hmi: start the local service (127.0.0.1 only) if it is not answering, then open the overview
rem in a Chrome app window (no address bar, own taskbar icon). Falls back to the default browser.
setlocal
set "PORT=8787"
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
curl -s -o nul --max-time 2 http://127.0.0.1:%PORT%/api/meta
set "DOWN=%ERRORLEVEL%"
if not "%DOWN%"=="0" start "system-hmi service" /min "%PY%" -X utf8 "%~dp0hmi.py" serve --port %PORT%
if not "%DOWN%"=="0" timeout /t 2 /nobreak >nul
start "" chrome --app=http://127.0.0.1:%PORT%/ --window-size=1500,900
if errorlevel 1 start "" http://127.0.0.1:%PORT%/
endlocal
