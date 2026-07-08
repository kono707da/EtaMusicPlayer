"""下载器：B站视频音频提取 → ffmpeg转码 → 标签写入 → 入库"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.plugins.bili_audio.bili_client import BiliClient
from app.plugins.bili_audio.database import SessionLocal
from app.plugins.bili_audio.models import BiliDownloadTask
from app.utils.tag_writer import write_tags_and_cover

logger = logging.getLogger("etamusic.plugins.bili_audio")

_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|\u3010\u3011\u300a\u300b\uff08\uff09]')


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(". ")


def _get_watch_dir_path(watch_dir_id: int) -> Optional[str]:
    try:
        from app.plugins.local_node.database import SessionLocal as LocalSession
        from app.plugins.local_node.models import WatchDir
    except ImportError:
        return None
    db = LocalSession()
    try:
        wd = db.get(WatchDir, watch_dir_id)
        return wd.path if wd else None
    finally:
        db.close()


def _trigger_local_node_scan() -> bool:
    try:
        from app.plugins.local_node.database import SessionLocal as LocalSession
        from app.plugins.local_node.models import ScanTask
        from app.plugins.local_node.scanner import run_scan
    except ImportError as e:
        logger.warning("无法导入 local_node 扫描模块: %s", e)
        return False
    db = LocalSession()
    try:
        task = ScanTask(status="pending", started_at=datetime.utcnow())
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id
        db.close()
        run_scan(task_id, watch_dir_id=None)
        return True
    except Exception as e:
        logger.warning("触发 local_node 扫描失败: %s", e)
        return False
    finally:
        try:
            db.close()
        except Exception:
            pass


def _find_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def _convert_to_audio(
    input_path: str, output_path: str, fmt: str = "mp3", bitrate: str = "192k"
) -> bool:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        logger.error("未找到 ffmpeg，无法转码")
        return False
    cmd = [
        ffmpeg,
        "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame" if fmt == "mp3" else "copy",
        "-ab", bitrate,
        "-ar", "44100",
        "-ac", "2",
        output_path,
    ]
    if fmt == "m4a":
        cmd = [
            ffmpeg,
            "-y",
            "-i", input_path,
            "-vn",
            "-acodec", "aac",
            "-ab", bitrate,
            "-ar", "44100",
            "-ac", "2",
            output_path,
        ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        if result.returncode != 0:
            logger.error("ffmpeg 转码失败: %s", result.stderr[:500])
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg 转码超时")
        return False
    except Exception as e:
        logger.error("ffmpeg 转码异常: %s", e)
        return False


def _worker(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.get(BiliDownloadTask, task_id)
        if task is None:
            return

        task.status = "running"
        task.progress = 0.0
        task.updated_at = datetime.utcnow()
        db.commit()

        from app.plugins.bili_audio.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        proxy = settings.get("proxy_url") or None
        sessdata = settings.get("sessdata") or None

        client = BiliClient(sessdata=sessdata, proxy_url=proxy)

        try:
            info = client.get_video_info(task.bvid)
        except Exception as e:
            task.status = "failed"
            task.error_message = f"获取视频信息失败: {e}"[:2000]
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        pages = info.get("pages", [])
        page_index = task.page_index
        if page_index >= len(pages):
            page_index = 0
        page = pages[page_index] if pages else {}
        cid = page.get("cid", info.get("cid", 0))
        page_title = page.get("part", info.get("title", ""))

        task.page_title = page_title
        task.title = task.title or info.get("title", task.bvid)
        task.upper_name = task.upper_name or info.get("owner", {}).get("name")
        task.upper_mid = task.upper_mid or info.get("owner", {}).get("mid")
        task.cover_url = task.cover_url or info.get("pic")
        task.source_url = f"https://www.bilibili.com/video/{task.bvid}"
        db.commit()

        audio_url, audio_mime = client.get_audio_url(
            task.bvid, cid, quality=task.audio_quality
        )
        if not audio_url:
            task.status = "failed"
            task.error_message = "无法获取音频流地址（可能需要登录Cookie）"
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        watch_dir_path = _get_watch_dir_path(task.target_watch_dir_id) if task.target_watch_dir_id else None
        if not watch_dir_path:
            task.status = "failed"
            task.error_message = f"监控目录 {task.target_watch_dir_id} 不存在"
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        upper_dir = _sanitize(task.upper_name or "unknown")
        title_dir = _sanitize(task.title or task.bvid)
        subdir = _sanitize(task.target_subdir or "B站音频")
        output_dir = Path(watch_dir_path) / subdir / upper_dir / title_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        tmp_m4s = output_dir / f".tmp_{task.bvid}_{page_index}.m4s"
        fmt = task.output_format or "mp3"
        final_name = _sanitize(page_title or task.title or task.bvid)
        final_path = output_dir / f"{final_name}.{fmt}"

        if final_path.exists():
            task.status = "completed"
            task.progress = 100.0
            task.saved_to = str(final_path)
            task.file_size = final_path.stat().st_size
            task.finished_at = datetime.utcnow()
            db.commit()
            _trigger_local_node_scan()
            return

        def on_progress(done: int, total: int) -> None:
            if total > 0:
                task.progress = round(done / total * 80, 1)
                task.updated_at = datetime.utcnow()
                try:
                    db.commit()
                except Exception:
                    pass

        try:
            client.download_audio_stream(audio_url, str(tmp_m4s), on_progress=on_progress)
        except Exception as e:
            task.status = "failed"
            task.error_message = f"下载音频流失败: {e}"[:2000]
            task.finished_at = datetime.utcnow()
            db.commit()
            if tmp_m4s.exists():
                tmp_m4s.unlink(missing_ok=True)
            return

        task.progress = 80.0
        task.updated_at = datetime.utcnow()
        db.commit()

        if not _convert_to_audio(str(tmp_m4s), str(final_path), fmt=fmt):
            task.status = "failed"
            task.error_message = "ffmpeg 转码失败（请确认已安装 ffmpeg）"
            task.finished_at = datetime.utcnow()
            db.commit()
            if tmp_m4s.exists():
                tmp_m4s.unlink(missing_ok=True)
            return

        tmp_m4s.unlink(missing_ok=True)

        task.progress = 90.0
        task.saved_to = str(final_path)
        task.file_size = final_path.stat().st_size
        task.updated_at = datetime.utcnow()
        db.commit()

        cover_bytes = None
        cover_mime = "image/jpeg"
        if task.cover_url:
            cover_bytes = client.download_cover(task.cover_url)
            if cover_bytes:
                cover_path = output_dir / "cover.jpg"
                try:
                    cover_path.write_bytes(cover_bytes)
                except Exception as e:
                    logger.warning("保存封面失败: %s", e)

        try:
            write_tags_and_cover(
                str(final_path),
                title=page_title or task.title,
                artist=task.upper_name,
                album=task.title,
                album_artist=task.upper_name,
                source_url=task.source_url,
                cover_bytes=cover_bytes,
                cover_mime=cover_mime,
            )
        except Exception as e:
            logger.warning("写入标签失败: %s", e)

        task.status = "completed"
        task.progress = 100.0
        task.finished_at = datetime.utcnow()
        db.commit()

        _trigger_local_node_scan()

    except Exception as e:
        logger.error("B站音频下载任务 %s 异常: %s", task_id, e, exc_info=True)
        try:
            task = db.get(BiliDownloadTask, task_id)
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
    with _lock:
        if task_id in _running_tasks:
            return
        t = threading.Thread(target=_worker, args=(task_id,), daemon=True)
        _running_tasks[task_id] = t
        t.start()


def cancel_download_task(task_id: int) -> bool:
    db = SessionLocal()
    try:
        task = db.get(BiliDownloadTask, task_id)
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
