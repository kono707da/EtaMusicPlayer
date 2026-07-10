@echo off
chcp 936 >nul 2>&1
setlocal EnableDelayedExpansion

echo ========================================
echo   EtaMusic Node - Environment Setup
echo ========================================
echo.

cd /d "%~dp0"

if exist "%~dp0venv\Scripts\python.exe" (
    echo [INFO] venv already exists: %~dp0venv\Scripts\python.exe
    set /p CONFIRM="Recreate? (y/N): "
    if /i not "!CONFIRM!"=="y" (
        echo [CANCEL] Keeping existing venv
        pause
        exit /b 0
    )
    echo [CLEAN] Removing old venv...
    rmdir /s /q "%~dp0venv"
)

REM Find base Python: prefer TRAE built-in, then system PATH (skip WindowsApps alias)
set "BASE_PY="
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "BASE_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    echo [Python] Using TRAE built-in Python: !BASE_PY!
) else (
    where python >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "delims=" %%i in ('where python') do (
            echo %%i | findstr /i "WindowsApps" >nul || (
                set "BASE_PY=%%i"
                goto :found_base
            )
        )
    )
    :found_base
    if "!BASE_PY!"=="" (
        echo [ERROR] Python not found. Install Python 3.10+ and add to PATH
        pause
        exit /b 1
    )
    echo [Python] Using system Python: !BASE_PY!
)

echo [CREATE] Initializing venv...
"!BASE_PY!" -m venv "%~dp0venv"
if !ERRORLEVEL! neq 0 (
    echo [ERROR] venv creation failed
    pause
    exit /b 1
)

echo [INSTALL] Upgrading pip...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
if !ERRORLEVEL! neq 0 (
    echo [ERROR] pip upgrade failed
    pause
    exit /b 1
)

echo [INSTALL] Installing dependencies...
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Dependency install failed, check network or requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Environment setup complete
echo ========================================
echo venv path: %~dp0venv
echo You can now run start.bat to launch the node
echo.
pause