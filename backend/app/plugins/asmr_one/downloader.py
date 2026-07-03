"""下载器：后台线程流式下载到 local_node watch_dir

工作流程：
1. 创建 DownloadTask 记录（pending）
2. 启动后台线程：依次下载每个文件到 {watch_dir_path}/{subdir}/{work_title}/{file_path}
3. 已存在且同大小的文件跳过
4. 全部完成后调用 local_node 的 /api/scan 触发扫描入库
5. 失败/部分失败：标记 partial 或 failed，错误信息写入 error_message
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.plugins.asmr_one.asmr_client import AsmrClient
from app.plugins.asmr_one.database import SessionLocal
from app.plugins.asmr_one.models import DownloadFileStatus, DownloadTask

logger = logging.getLogger("etamusic.plugins.asmr_one")

# 单线程下载（避免对 asmr.one 造成压力）
_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}


# Windows 文名非法字符替换
_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _build_target_path(
    watch_dir_path: str,
    subdir: Optional[str],
    work_title: str,
    file_rel_path: str,
) -> Path:
    """构造目标文件绝对路径"""
    parts = [watch_dir_path]
    if subdir:
        parts.append(subdir.strip("/\\"))
    parts.append(_sanitize(work_title))
    # file_rel_path 是用 / 分隔的相对路径
    for seg in file_rel_path.split("/"):
        if seg:
            parts.append(_sanitize(seg))
    return Path(*parts)


def _get_local_node_token() -> Optional[str]:
    """获取 local_node 的 admin token（与 /api/plugins/local-node/status 同逻辑）"""
    try:
        from app.plugins_manager.models import Plugin
        from app.plugins_manager.routers import _loaded_in_process
        from app.security import create_access_token
        from app.plugins.local_node.database import (
            SessionLocal as LocalSession,
        )
        from app.plugins.local_node.models import User as LocalUser
    except ImportError:
        return None

    db_local = LocalSession()
    try:
        admin = db_local.query(LocalUser).filter(LocalUser.username == "admin").one_or_none()
        if admin is None:
            return None
        return create_access_token(admin.id)
    finally:
        db_local.close()


def _get_watch_dir_path(watch_dir_id: int) -> Optional[str]:
    """通过 local_node API 查询监控目录绝对路径"""
    try:
        from app.plugins.local_node.database import SessionLocal as LocalSession
        from app.plugins.local_node.models import WatchDir
    except ImportError:
        return None

    db_local = LocalSession()
    try:
        wd = db_local.get(WatchDir, watch_dir_id)
        return wd.path if wd else None
    finally:
        db_local.close()


def _trigger_local_node_scan(token: str) -> bool:
    """调用 local_node 的 /api/scan 触发扫描"""
    import requests

    try:
        r = requests.post(
            "http://127.0.0.1:8000/local_node/api/scan",
            json={},
            headers={"Authorization": f"Bearer {token}"},
            timeout=300,
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.warning("触发 local_node 扫描失败: %s", e)
        return False


def _download_one(
    client: AsmrClient,
    url: str,
    target: Path,
    on_progress=None,
) -> int:
    """下载单个文件到 target，返回下载字节数

    on_progress(done_bytes: int, total_bytes: int)
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    # 先 HEAD 获取总大小
    total = 0
    try:
        headers = client.head(url)
        total = int(headers.get("Content-Length") or 0)
    except Exception:
        pass

    # 已存在且同大小跳过
    if target.exists() and total > 0 and target.stat().st_size == total:
        if on_progress:
            on_progress(total, total)
        return total

    done = 0
    tmp = target.with_suffix(target.suffix + ".part")
    with open(tmp, "wb") as f:
        for chunk in client.stream_download(url):
            f.write(chunk)
            done += len(chunk)
            if on_progress:
                on_progress(done, total)
    os.replace(tmp, target)
    return done


def _worker(task_id: int) -> None:
    """后台线程入口"""
    db = SessionLocal()
    try:
        task = db.get(DownloadTask, task_id)
        if task is None:
            return

        task.status = "running"
        task.updated_at = datetime.utcnow()
        db.commit()

        # 取出文件清单
        files: list[dict] = task.files_json or []
        selected: set[str] = set(task.selected_paths or [])
        if selected:
            files = [f for f in files if f.get("path") in selected]

        task.total_files = len(files)
        db.commit()

        # 查询目标 watch_dir 路径
        watch_dir_path = _get_watch_dir_path(task.target_watch_dir_id)
        if not watch_dir_path:
            task.status = "failed"
            task.error_message = f"watch_dir {task.target_watch_dir_id} 不存在"
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        # 创建客户端
        from app.plugins.asmr_one.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        proxy = settings.get("proxy_url") or "http://127.0.0.1:7897"
        client = AsmrClient(proxy_url=proxy)

        completed = 0
        skipped = 0
        failed = 0
        errors: list[str] = []

        # 清理旧 file status
        db.query(DownloadFileStatus).filter(DownloadFileStatus.task_id == task_id).delete()
        db.commit()

        # 创建 file status 记录
        for f in files:
            db.add(
                DownloadFileStatus(
                    task_id=task_id,
                    file_path=f.get("path", ""),
                    status="pending",
                    size=int(f.get("size") or 0),
                    done=0,
                )
            )
        db.commit()

        for idx, f in enumerate(files):
            # 重新查询任务，检查是否被取消
            db.refresh(task)
            if task.status == "canceled":
                return

            file_path = f.get("path", "")
            url = f.get("url")
            file_status = (
                db.query(DownloadFileStatus)
                .filter(
                    DownloadFileStatus.task_id == task_id,
                    DownloadFileStatus.file_path == file_path,
                )
                .one_or_none()
            )

            task.current_file = file_path
            task.current_file_size = int(f.get("size") or 0)
            task.current_file_done = 0
            task.updated_at = datetime.utcnow()
            if file_status:
                file_status.status = "downloading"
                file_status.updated_at = datetime.utcnow()
            db.commit()

            if not url:
                failed += 1
                if file_status:
                    file_status.status = "failed"
                    file_status.error = "无下载链接"
                errors.append(f"{file_path}: 无下载链接")
                continue

            target = _build_target_path(
                watch_dir_path=watch_dir_path,
                subdir=task.target_subdir,
                work_title=task.work_title,
                file_rel_path=file_path,
            )

            # 跳过已存在且同大小
            if target.exists() and task.current_file_size > 0 and target.stat().st_size == task.current_file_size:
                skipped += 1
                if file_status:
                    file_status.status = "skipped"
                    file_status.done = task.current_file_size
                    file_status.saved_to = str(target)
                continue

            try:
                def on_progress(done: int, total: int) -> None:
                    task.current_file_done = done
                    if file_status:
                        file_status.done = done
                    # 不每次 commit，每 5% commit 一次
                downloaded = _download_one(client, url, target, on_progress=on_progress)
                completed += 1
                if file_status:
                    file_status.status = "completed"
                    file_status.done = downloaded
                    file_status.saved_to = str(target)
            except Exception as e:
                failed += 1
                if file_status:
                    file_status.status = "failed"
                    file_status.error = str(e)[:500]
                errors.append(f"{file_path}: {e}")
                logger.warning("下载失败 %s: %s", file_path, e)

            task.completed_files = completed
            task.skipped_files = skipped
            task.failed_files = failed
            task.updated_at = datetime.utcnow()
            db.commit()

        # 最终状态
        if failed == 0:
            task.status = "completed"
        elif completed == 0 and skipped == 0:
            task.status = "failed"
        else:
            task.status = "partial"
        task.error_message = "\n".join(errors[:20]) if errors else None
        task.finished_at = datetime.utcnow()
        task.current_file = None
        db.commit()

        # 触发扫描
        if completed > 0 or skipped > 0:
            token = _get_local_node_token()
            if token:
                _trigger_local_node_scan(token)

    except Exception as e:
        logger.error("下载任务 %s 异常: %s", task_id, e, exc_info=True)
        try:
            task = db.get(DownloadTask, task_id)
            if task:
                task.status = "failed"
                task.error_message = f"任务异常: {e}"[:2000]
                task.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        with _lock:
            _running_tasks.pop(task_id, None)


def start_download_task(task_id: int) -> None:
    """启动后台下载线程"""
    with _lock:
        if task_id in _running_tasks:
            return
        t = threading.Thread(target=_worker, args=(task_id,), daemon=True)
        _running_tasks[task_id] = t
        t.start()


def cancel_download_task(task_id: int) -> bool:
    """请求取消任务（标记为 canceled，线程下次循环检测到会退出）"""
    db = SessionLocal()
    try:
        task = db.get(DownloadTask, task_id)
        if task is None:
            return False
        if task.status not in ("pending", "running"):
            return False
        task.status = "canceled"
        task.finished_at = datetime.utcnow()
        db.commit()
        return True
    finally:
        db.close()
