@echo off
chcp 936 >nul 2>&1
setlocal EnableDelayedExpansion

echo ========================================
echo   EtaMusic Web - 环境初始化
echo ========================================
echo.

cd /d "%~dp0"

if exist "%~dp0web\backend\venv\Scripts\python.exe" (
    echo [提示] venv 已存在: %~dp0web\backend\venv\Scripts\python.exe
    set /p CONFIRM="是否重建? (y/N): "
    if /i not "!CONFIRM!"=="y" (
        echo [取消] 保留现有 venv
        pause
        exit /b 0
    )
    echo [清理] 删除旧 venv...
    rmdir /s /q "%~dp0web\backend\venv"
)

REM 查找基础 Python：优先 TRAE 自带，最后系统 PATH（跳过 WindowsApps 占位符）
set "BASE_PY="
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "BASE_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    echo [Python] 使用 TRAE 自带 Python: !BASE_PY!
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
        echo [错误] 未找到可用的 Python，请安装 Python 3.10+ 并加入 PATH
        pause
        exit /b 1
    )
    echo [Python] 使用系统 Python: !BASE_PY!
)

echo [创建] 初始化 venv...
"!BASE_PY!" -m venv "%~dp0web\backend\venv"
if !ERRORLEVEL! neq 0 (
    echo [错误] venv 创建失败
    pause
    exit /b 1
)

echo [安装] 升级 pip...
"%~dp0web\backend\venv\Scripts\python.exe" -m pip install --upgrade pip
if !ERRORLEVEL! neq 0 (
    echo [错误] pip 升级失败
    pause
    exit /b 1
)

echo [安装] 安装项目依赖...
"%~dp0web\backend\venv\Scripts\python.exe" -m pip install -r "%~dp0web\backend\requirements.txt"
if !ERRORLEVEL! neq 0 (
    echo [错误] 依赖安装失败，请检查网络或 requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo   环境初始化完成
echo ========================================
echo venv 路径: %~dp0web\backend\venv
echo 现在可以运行 start.bat 启动 Web 服务
echo.
pause