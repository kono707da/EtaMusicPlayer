@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
set "TRAE_NODE=%APPDATA%\TRAE SOLO CN\ModularData\ai-agent\vm\tools\node"
set "COMFY_PY=C:\Users\kono707da\Documents\ComfyUI-aki-v1.7\python"

rem ---- Resolve python ----
set "PY_CMD="
where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD if exist "%COMFY_PY%\python.exe" set "PY_CMD=%COMFY_PY%\python.exe"

if not defined PY_CMD (
    echo ERROR: python not found.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

rem ---- Add TRAE bundled node to PATH if system npm is missing ----
where npm >nul 2>nul
if errorlevel 1 if exist "%TRAE_NODE%\npm.cmd" set "PATH=%TRAE_NODE%;%PATH%"

where npm >nul 2>nul
if errorlevel 1 (
    echo ERROR: npm not found in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

rem ---- Kill leftover EtaMusic backend on port 8000 (only our own uvicorn) ----
echo Checking port 8000 for stale EtaMusic backend...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%kill_stale_port.ps1"
set "PS_EXIT=%errorlevel%"
if "%PS_EXIT%"=="0" (
    echo Port 8000 is free.
) else if "%PS_EXIT%"=="1" (
    echo ERROR: failed to release port 8000 from our own stale process.
    echo Backend may fail to start. Close any running EtaMusic instance and retry.
    pause
    exit /b 1
) else (
    echo WARNING: port 8000 is held by another program.
    echo Backend may fail to start. Close that program or change port in config.yaml.
)

echo ============================================
echo   EtaMusicPlayer Launcher (single process)
echo ============================================
echo Using python: %PY_CMD%
echo.

rem ---- Build frontend if dist/ does not exist ----
if not exist "%ROOT%frontend\dist\index.html" (
    echo [1/2] Building frontend ^(first time or dist missing^)...
    pushd "%ROOT%frontend"
    call npm run build
    popd
    if not exist "%ROOT%frontend\dist\index.html" (
        echo ERROR: Frontend build failed.
        pause
        exit /b 1
    )
    echo Frontend built successfully.
) else (
    echo [1/2] Frontend dist/ already exists, skipping build.
    echo ^(Delete frontend\dist\ to force rebuild, or run: cd frontend ^& npm run build^)
)

rem ---- Start backend (serves API + static frontend) ----
echo [2/2] Starting server on http://0.0.0.0:8000 ...
echo.
echo Open in browser:
echo   Local:   http://127.0.0.1:8000
echo   Network: http://192.168.3.94:8000
echo.
echo Press Ctrl+C to stop.
echo.

cd /d "%ROOT%backend"
"%PY_CMD%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal
