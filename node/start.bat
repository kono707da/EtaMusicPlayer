@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo ========================================
echo   EtaMusic Node - 独立节点启动脚本
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
powershell -ExecutionPolicy Bypass -File "..\kill_stale_port.ps1"
if %ERRORLEVEL% equ 2 (
    echo [错误] 端口 8001 被其他程序占用
    pause
    exit /b 1
)

REM 启动节点
echo [启动] EtaMusic Node (端口 8001^)
cd /d "%~dp0"
python -m uvicorn eta_node.standalone:app --host 0.0.0.0 --port 8001
pause
