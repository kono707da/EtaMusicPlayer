"""端口冲突检测与处理

启动前确保端口可用：
- 端口空闲：直接返回
- 端口被本应用（eta_node.exe）占用：杀掉旧进程后返回
- 端口被其他程序占用：报错退出，提示用户

跨平台支持 Windows（netstat/tasklist/taskkill）和 POSIX（lsof/ps/kill）。
仅使用标准库，避免引入新依赖。
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time


def _is_port_free(host: str, port: int) -> bool:
    """检测端口是否空闲（没有进程在监听）。

    用 connect 检测：能连上 127.0.0.1:port 说明有进程在监听。
    比 bind 检测更可靠（Windows 上 SO_REUSEADDR 会让 bind 检测失效）。
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        # connect_ex 返回 0 = 连接成功 = 端口被占用
        # 返回非 0 = 连接失败 = 端口空闲
        return sock.connect_ex(("127.0.0.1", port)) != 0
    finally:
        sock.close()


def _find_listening_pids_windows(port: int) -> list[str]:
    """Windows: 用 netstat 找出监听该端口的 PID 列表。"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
            timeout=5,
        )
    except Exception:
        return []
    pids: list[str] = []
    for line in result.stdout.splitlines():
        # 行格式: TCP  0.0.0.0:8001  0.0.0.0:0  LISTENING  12345
        parts = line.split()
        if len(parts) < 5:
            continue
        local_addr = parts[1]
        state = parts[3]
        pid = parts[4]
        if not local_addr.endswith(f":{port}"):
            continue
        if state != "LISTENING":
            continue
        if pid == "0":
            continue
        pids.append(pid)
    # 去重保序
    return list(dict.fromkeys(pids))


def _find_listening_pids_posix(port: int) -> list[str]:
    """POSIX: 优先用 lsof，回退到 ss。"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [p for p in result.stdout.split() if p]
    except FileNotFoundError:
        pass
    except Exception:
        pass
    # 回退到 ss
    try:
        result = subprocess.run(
            ["ss", "-tlnpH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        pids: list[str] = []
        for line in result.stdout.splitlines():
            if f":{port} " not in line and not line.rstrip().endswith(f":{port}"):
                continue
            if "pid=" not in line:
                continue
            pid_part = line.split("pid=", 1)[1].split(",")[0]
            pids.append(pid_part)
        return list(dict.fromkeys(pids))
    except Exception:
        return []


def _get_process_name_windows(pid: str) -> str:
    """Windows: 用 tasklist 查 PID 对应的进程名（小写）。"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
            timeout=5,
        )
        line = result.stdout.strip()
        if not line or line.startswith("信息:") or line.startswith("INFO:"):
            return ""
        return line.split(",")[0].strip('"').lower()
    except Exception:
        return ""


def _get_process_name_posix(pid: str) -> str:
    """POSIX: 用 ps 查 PID 对应的进程名（小写）。"""
    try:
        result = subprocess.run(
            ["ps", "-p", pid, "-o", "comm="],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip().lower()
    except Exception:
        return ""


def _kill_pid_windows(pid: str) -> bool:
    """Windows: taskkill 强杀进程。"""
    try:
        result = subprocess.run(
            ["taskkill", "/PID", pid, "/F"],
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="ignore",
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _kill_pid_posix(pid: str) -> bool:
    """POSIX: kill -9 强杀进程。"""
    try:
        os.kill(int(pid), 9)
        return True
    except Exception:
        return False


def _is_self_process(name: str) -> bool:
    """判断进程名是否是 eta_node 自身（打包 exe 或源码运行）。

    开发模式下可能是 python/python.exe 跑 standalone.py，
    这种情况不自动杀，避免误杀其他 python 进程。
    """
    if not name:
        return False
    name = name.lower()
    return name in ("eta_node.exe", "eta_node")


def ensure_port_available(host: str, port: int, max_wait_seconds: int = 10) -> None:
    """启动前确保端口可用。

    - 端口空闲：直接返回
    - 端口被 eta_node 自身占用：杀掉旧进程，等待端口释放
    - 端口被其他程序占用：打印错误信息并 sys.exit(1)

    Args:
        host: 监听地址（如 "0.0.0.0"）
        port: 监听端口
        max_wait_seconds: 杀掉旧进程后等待端口释放的最大秒数
    """
    if _is_port_free(host, port):
        return

    print(f"[port] Port {port} is already in use, finding occupant...")

    is_windows = sys.platform == "win32"
    if is_windows:
        pids = _find_listening_pids_windows(port)
        get_name = _get_process_name_windows
        kill_pid = _kill_pid_windows
    else:
        pids = _find_listening_pids_posix(port)
        get_name = _get_process_name_posix
        kill_pid = _kill_pid_posix

    if not pids:
        print(f"[port] ERROR: Cannot find which process uses port {port}.")
        print(f"[port] Please check manually or change port in config.yaml.")
        sys.exit(1)

    self_pids: list[tuple[str, str]] = []
    foreign: list[tuple[str, str]] = []
    for pid in pids:
        name = get_name(pid)
        if _is_self_process(name):
            self_pids.append((pid, name))
        else:
            foreign.append((pid, name))

    # 杀掉自己的旧进程
    for pid, name in self_pids:
        if kill_pid(pid):
            print(f"[port] Killed stale eta_node process (PID {pid}).")
        else:
            print(f"[port] WARNING: Failed to kill PID {pid} ({name}).")

    # 其他程序占用：报错退出
    if foreign:
        print(f"[port] ERROR: Port {port} is occupied by other program(s):")
        for pid, name in foreign:
            print(f"[port]   PID {pid}: {name}")
        print(f"[port] Please close them or change port in config.yaml.")
        sys.exit(1)

    # 等待端口释放
    for _ in range(max_wait_seconds * 2):
        time.sleep(0.5)
        if _is_port_free(host, port):
            print(f"[port] Port {port} is now free.")
            return

    print(f"[port] ERROR: Port {port} still in use after {max_wait_seconds}s.")
    sys.exit(1)
