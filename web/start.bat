@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo ========================================
echo   EtaMusic Web - 启动脚本
echo ========================================
echo.

REM 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python，请安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查端口
powershell -ExecutionPolicy Bypass -File "%~dp0..\kill_stale_port.ps1"
if %ERRORLEVEL% equ 2 (
    echo [错误] 端口 8000 被其他程序占用
    pause
    exit /b 1
)

REM 检查前端构建产物
if not exist "%~dp0frontend\dist\index.html" (
    echo [构建] 前端构建产物不存在，开始构建...
    where npm >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [错误] 未找到 npm，请安装 Node.js
        pause
        exit /b 1
    )
    pushd "%~dp0frontend"
    call npm install
    call npm run build
    popd
)

REM 启动 Web 骨架
echo [启动] EtaMusic Web (端口 8000)
cd /d "%~dp0backend"
python -m uvicorn eta_web.main:app --host 0.0.0.0 --port 8000
pause
