@echo off
chcp 936 >nul 2>&1
setlocal EnableDelayedExpansion

REM 设置 Python 输出编码为 GBK，避免中文乱码
set "PYTHONIOENCODING=gbk"
set "PYTHONUTF8=0"

echo ========================================
echo   EtaMusic Node - 独立节点启动脚本
echo ========================================
echo.

cd /d "%~dp0"

REM 查找可用 Python：优先项目 venv，其次 TRAE 自带 Python，最后系统 PATH（跳过 WindowsApps 占位符）
set "PYTHON_EXE="
if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
    echo [Python] 使用项目 venv: !PYTHON_EXE!
) else if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    echo [Python] 使用 TRAE 自带 Python: !PYTHON_EXE!
    echo [警告] 未找到 venv，建议先运行 setup_env.bat 创建虚拟环境
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
        echo [错误] 未找到可用的 Python，请执行以下任一操作：
        echo        1. 运行 setup_env.bat 自动创建 venv
        echo        2. 手动安装 Python 3.10+ 并加入 PATH
        pause
        exit /b 1
    )
    echo [Python] 使用系统 Python: !PYTHON_EXE!
)

REM 确保数据目录存在
if not exist "%~dp0data" (
    mkdir "%~dp0data"
    echo [初始化] 创建数据目录: %~dp0data
)

REM 检查端口 8001：本应用占用则杀掉重启，其他应用占用则报错退出
powershell -ExecutionPolicy Bypass -File "%~dp0..\kill_stale_port.ps1" -Port 8001
if !ERRORLEVEL! equ 2 (
    echo [错误] 端口 8001 被其他程序占用，请先释放该端口
    pause
    exit /b 1
)

REM 启动节点
echo [启动] EtaMusic Node (端口 8001)
"!PYTHON_EXE!" -m uvicorn eta_node.standalone:app --host 0.0.0.0 --port 8001
pause