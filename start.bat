@echo off
chcp 936 >nul 2>&1
setlocal EnableDelayedExpansion

set "PYTHONIOENCODING=gbk"
set "PYTHONUTF8=0"

echo ========================================
echo   EtaMusic - Quick Start
echo ========================================
echo.

cd /d "%~dp0"

REM Find Python: prefer web/backend venv, then TRAE built-in, then system PATH (skip WindowsApps alias)
set "PYTHON_EXE="
if exist "%~dp0web\backend\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0web\backend\venv\Scripts\python.exe"
    echo [Python] Using web/backend venv: !PYTHON_EXE!
) else if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    echo [Python] Using TRAE built-in Python: !PYTHON_EXE!
    echo [WARN] venv not found, run setup_env.bat first
) else (
    where python >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "delims=" %%i in ('where python') do (
            echo %%i | findstr /i "WindowsApps" >nul || (
                set "PYTHON_EXE=%%i"
                goto :found_python
            )
        )
    )
    :found_python
    if "!PYTHON_EXE!"=="" (
        echo [ERROR] Python not found. Please do one of the following:
        echo         1. Run setup_env.bat to create a venv
        echo         2. Install Python 3.10+ and add to PATH
        pause
        exit /b 1
    )
    echo [Python] Using system Python: !PYTHON_EXE!
)

REM Check port 8000: kill our stale process, abort if held by others
powershell -ExecutionPolicy Bypass -File "%~dp0kill_stale_port.ps1" -Port 8000
if !ERRORLEVEL! equ 2 (
    echo [ERROR] Port 8000 is occupied by another program
    pause
    exit /b 1
)

REM Check frontend build
if not exist "%~dp0web\frontend\dist\index.html" (
    echo [BUILD] Frontend dist not found, building...
    where npm >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] npm not found, please install Node.js
        pause
        exit /b 1
    )
    pushd "%~dp0web\frontend"
    call npm install
    call npm run build
    popd
)

REM Ensure data directory exists
if not exist "%~dp0web\backend\data" (
    mkdir "%~dp0web\backend\data"
    echo [INIT] Created data directory: %~dp0web\backend\data
)

REM Start web backend
echo [START] EtaMusic Web (port 8000)
cd /d "%~dp0web\backend"
"!PYTHON_EXE!" -m uvicorn eta_web.main:app --host 0.0.0.0 --port 8000
pause