"""EtaMusic 访问端启动入口

支持插件管理触发的优雅重启：
- 用子进程方式启动 uvicorn
- 当 /api/plugins/restart 被调用时，uvicorn 子进程通过 os._exit(0) 退出
- 本入口检测到 data/restart.flag 后重新启动子进程
- 循环最多 10 次以防死循环
"""
import os
import subprocess
import sys
from pathlib import Path

from app.config import settings

# 重启标志文件
RESTART_FLAG = Path(__file__).resolve().parent / "data" / "restart.flag"
MAX_RESTARTS = 10


def _consume_restart_flag() -> bool:
    """检查并消费重启标志。返回 True 表示需要重启。"""
    if RESTART_FLAG.exists():
        try:
            RESTART_FLAG.unlink()
        except OSError:
            pass
        return True
    return False


def main() -> None:
    """用子进程方式启动 uvicorn，支持重启循环"""
    backend_dir = Path(__file__).resolve().parent
    restarts = 0
    while True:
        print(f"[run.py] 启动 uvicorn（第 {restarts + 1} 次）...")
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", settings.host,
                "--port", str(settings.port),
            ],
            cwd=str(backend_dir),
        )
        # 等待 uvicorn 子进程退出
        proc.wait()
        # 检查重启标志
        if _consume_restart_flag():
            restarts += 1
            if restarts > MAX_RESTARTS:
                print(f"[run.py] 已达到最大重启次数 {MAX_RESTARTS}，停止")
                break
            print(f"[run.py] 检测到重启标志，第 {restarts} 次重启...")
            continue
        break


if __name__ == "__main__":
    main()
