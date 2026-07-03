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
from app.plugins.asmr_one.tag_writer import (
    AUDIO_EXTS,
    write_cover_to_file,
    write_metadata_to_file,
)

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


def _trigger_local_node_scan() -> bool:
    """直接调用 local_node 的 run_scan 触发扫描（同进程，避免 HTTP 自调用）"""
    try:
        from app.plugins.local_node.database import SessionLocal as LocalSession
        from app.plugins.local_node.models import ScanTask
        from app.plugins.local_node.scanner import run_scan
    except ImportError as e:
        logger.warning("无法导入 local_node 扫描模块: %s", e)
        return False

    db_local = LocalSession()
    try:
        task = ScanTask(status="pending", started_at=datetime.utcnow())
        db_local.add(task)
        db_local.commit()
        db_local.refresh(task)
        task_id = task.id
        db_local.close()

        run_scan(task_id, watch_dir_id=None)
        return True
    except Exception as e:
        logger.warning("触发 local_node 扫描失败: %s", e)
        return False
    finally:
        try:
            db_local.close()
        except Exception:
            pass


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


def _apply_metadata_and_cover(db: Session, task: DownloadTask, client: AsmrClient) -> None:
    """下载完成后：把专辑/艺术家等元数据与封面回写到音频文件标签。

    metadata_json 结构：
      {album, artist, album_artist, cover_type}
    cover_type 取值：main / sam / 240x240，None 表示不写封面
    """
    meta = task.metadata_json or {}
    if not meta:
        return

    album = meta.get("album")
    artist = meta.get("artist")
    album_artist = meta.get("album_artist")
    cover_type = meta.get("cover_type")  # None 表示不嵌入封面

    # 取出所有已下载完成的文件
    file_statuses = (
        db.query(DownloadFileStatus)
        .filter(
            DownloadFileStatus.task_id == task.id,
            DownloadFileStatus.status.in_(["completed", "skipped"]),
            DownloadFileStatus.saved_to.isnot(None),
        )
        .all()
    )

    # 仅处理音频文件
    audio_files = [
        fs for fs in file_statuses
        if fs.saved_to and Path(fs.saved_to).suffix.lower() in AUDIO_EXTS
    ]

    if not audio_files:
        return

    # 1. 回写元数据（专辑 / 艺术家 / 专辑艺术家）
    if album or artist or album_artist:
        for fs in audio_files:
            try:
                write_metadata_to_file(
                    fs.saved_to,
                    title=None,  # 不覆盖单文件标题（保留原文件名）
                    artist=artist,
                    album=album,
                    album_artist=album_artist,
                )
            except Exception as e:
                logger.warning("回写元数据失败 %s: %s", fs.saved_to, e)
        logger.info("任务 %s: 已为 %d 个音频文件回写元数据", task.id, len(audio_files))

    # 2. 回写封面
    if cover_type and not task.cover_applied:
        try:
            cover_bytes = client.get_cover_bytes(task.work_id, cover_type=cover_type)
            mime = "image/jpeg"  # asmr.one cover API 返回 jpeg
            ok_count = 0
            for fs in audio_files:
                try:
                    if write_cover_to_file(fs.saved_to, cover_bytes, mime):
                        ok_count += 1
                except Exception as e:
                    logger.warning("回写封面失败 %s: %s", fs.saved_to, e)
            task.cover_applied = True
            db.commit()
            logger.info("任务 %s: 已为 %d/%d 个音频文件嵌入封面", task.id, ok_count, len(audio_files))
        except Exception as e:
            logger.warning("任务 %s: 获取封面字节失败: %s", task.id, e)


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

        # 下载完成后：把元数据（专辑/艺术家）与封面回写到音频文件标签
        if completed > 0 or skipped > 0:
            _apply_metadata_and_cover(db, task, client)

        # 触发扫描
        if completed > 0 or skipped > 0:
            _trigger_local_node_scan()

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
