"""下载器：后台线程流式下载到 local_node watch_dir

工作流程：
1. 创建 BiliDownloadTask 记录（pending）
2. 启动后台线程：依次下载每个文件到 {watch_dir_path}/{subdir}/{title}/{file_path}
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

from eta_bili.bili_client import BiliClient
from eta_bili.database import SessionLocal
from eta_bili.models import BiliDownloadTask

try:
    from eta_shared.tag_writer import write_tags_and_cover
except ImportError:
    write_tags_and_cover = None

logger = logging.getLogger("etamusic.plugins.bili_audio")

_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _build_target_path(
    watch_dir_path: str,
    subdir: Optional[str],
    title: str,
    file_rel_path: str,
) -> Path:
    parts = [watch_dir_path]
    if subdir:
        parts.append(subdir.strip("/\\"))
    parts.append(_sanitize(title))
    for seg in file_rel_path.split("/"):
        if seg:
            parts.append(_sanitize(seg))
    return Path(*parts)


def _get_watch_dir_path(watch_dir_id: int) -> Optional[str]:
    try:
        from eta_node.database import SessionLocal as LocalSession
        from eta_node.models import WatchDir
    except ImportError:
        return None

    db_local = LocalSession()
    try:
        wd = db_local.get(WatchDir, watch_dir_id)
        return wd.path if wd else None
    finally:
        db_local.close()


def _trigger_local_node_scan() -> bool:
    try:
        from eta_node.database import SessionLocal as LocalSession
        from eta_node.models import ScanTask
        from eta_node.scanner import run_scan
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


def _create_album_playlist(db: Session, task: BiliDownloadTask) -> Optional[int]:
    try:
        from eta_node.database import SessionLocal as LocalSession
        from eta_node.models import Playlist, PlaylistItem, Track, SYSTEM_PLAYLIST_INBOX
    except ImportError as e:
        logger.warning("无法导入 local_node 模块: %s", e)
        return None

    db_local = LocalSession()
    try:
        from eta_bili.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        audio_exts = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".ape"}

        saved_dir = Path(task.target_subdir or "") / _sanitize(task.title) if task.target_subdir else Path(_sanitize(task.title))
        watch_dir_path = _get_watch_dir_path(task.target_watch_dir_id)
        if not watch_dir_path:
            return None

        target_base = Path(watch_dir_path)
        if task.target_subdir:
            target_base = target_base / task.target_subdir.strip("/\\")
        target_base = target_base / _sanitize(task.title)

        if not target_base.exists():
            logger.info("任务 %s: 下载目录不存在 %s，跳过播放列表创建", task.id, target_base)
            return None

        audio_files = [f for f in target_base.rglob("*") if f.is_file() and f.suffix.lower() in audio_exts]
        if not audio_files:
            return None

        abs_paths = [str(f.resolve()) for f in audio_files]
        tracks = (
            db_local.query(Track)
            .filter(Track.abs_path.in_(abs_paths))
            .all()
        )
        if not tracks:
            logger.warning(
                "任务 %s: 未在 local_node 找到对应 Track（可能扫描未完成），跳过播放列表创建",
                task.id,
            )
            return None

        from eta_node.models import User

        admin = db_local.query(User).filter(User.is_admin.is_(True)).first()
        if admin is None:
            logger.warning("任务 %s: local_node 无 admin 用户，跳过播放列表创建", task.id)
            return None

        playlist_name = task.title or f"BiliAudio {task.auid}"
        pl = (
            db_local.query(Playlist)
            .filter(
                Playlist.owner_id == admin.id,
                Playlist.name == playlist_name,
            )
            .one_or_none()
        )
        if pl is None:
            pl = Playlist(
                name=playlist_name,
                owner_id=admin.id,
                is_system=False,
                description=f"bilibili audio auid={task.auid}",
            )
            db_local.add(pl)
            db_local.commit()
            db_local.refresh(pl)
            logger.info("任务 %s: 已创建播放列表 '%s' (id=%s)", task.id, playlist_name, pl.id)
        else:
            logger.info("任务 %s: 播放列表 '%s' 已存在 (id=%s)，追加曲目", task.id, playlist_name, pl.id)

        max_pos = (
            db_local.query(PlaylistItem.position)
            .filter(PlaylistItem.playlist_id == pl.id)
            .order_by(PlaylistItem.position.desc())
            .first()
        )
        next_pos = (max_pos[0] + 1) if max_pos else 0

        added = 0
        for t in tracks:
            exists = (
                db_local.query(PlaylistItem)
                .filter(
                    PlaylistItem.playlist_id == pl.id,
                    PlaylistItem.track_id == t.id,
                )
                .one_or_none()
            )
            if exists:
                continue
            db_local.add(
                PlaylistItem(
                    playlist_id=pl.id,
                    track_id=t.id,
                    position=next_pos,
                )
            )
            next_pos += 1
            added += 1
        db_local.commit()
        logger.info(
            "任务 %s: 播放列表 '%s' 新增 %d/%d 首曲目",
            task.id, playlist_name, added, len(tracks),
        )
        return pl.id
    except Exception as e:
        logger.warning("任务 %s: 创建播放列表失败: %s", task.id, e)
        return None
    finally:
        db_local.close()


def _download_one(
    client: BiliClient,
    url: str,
    target: Path,
    on_progress=None,
) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    try:
        r = client.session.head(url, timeout=30, allow_redirects=True)
        total = int(r.headers.get("Content-Length") or 0)
    except Exception:
        pass

    if target.exists() and total > 0 and target.stat().st_size == total:
        if on_progress:
            on_progress(total, total)
        return total

    done = 0
    tmp = target.with_suffix(target.suffix + ".part")
    with client.stream_download(url) as resp:
        for chunk in resp.iter_content(chunk_size=65536):
            tmp.write(chunk)
            done += len(chunk)
            if on_progress:
                on_progress(done, total)
    os.replace(tmp, target)
    return done


def _apply_metadata_and_cover(
    db: Session,
    task: BiliDownloadTask,
    client: BiliClient,
) -> None:
    if write_tags_and_cover is None:
        logger.warning("eta_shared 未安装，跳过元数据/封面回写")
        return

    meta = task.metadata_json or {}
    if not meta:
        return

    album = meta.get("title")
    artist = meta.get("artist")
    album_artist = meta.get("album_artist")
    source_url = meta.get("source_url")
    cover_url = meta.get("cover_url")

    has_meta = any(v for v in (album, artist, album_artist, source_url))

    watch_dir_path = _get_watch_dir_path(task.target_watch_dir_id)
    if not watch_dir_path:
        return

    target_base = Path(watch_dir_path)
    if task.target_subdir:
        target_base = target_base / task.target_subdir.strip("/\\")
    target_base = target_base / _sanitize(task.title)

    if not target_base.exists():
        return

    audio_exts = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".ape"}
    audio_files = [f for f in target_base.rglob("*") if f.is_file() and f.suffix.lower() in audio_exts]

    if not audio_files:
        return

    cover_bytes = None
    cover_mime = "image/jpeg"
    if cover_url and not task.cover_applied:
        try:
            r = client.session.get(cover_url, timeout=30)
            r.raise_for_status()
            cover_bytes = r.content
            ct = r.headers.get("Content-Type", "")
            if "png" in ct:
                cover_mime = "image/png"
        except Exception as e:
            logger.warning("任务 %s: 获取封面失败: %s", task.id, e)

    ok_meta = 0
    ok_cover = 0
    for af in audio_files:
        try:
            success = write_tags_and_cover(
                str(af),
                title=None,
                artist=artist,
                album=album,
                album_artist=album_artist,
                source_url=source_url,
                cover_bytes=cover_bytes,
                cover_mime=cover_mime,
            )
            if success:
                ok_meta += 1
                if cover_bytes:
                    ok_cover += 1
        except Exception as e:
            logger.warning("回写标签/封面失败 %s: %s", af, e)

    if ok_meta > 0:
        logger.info(
            "任务 %s: 已为 %d/%d 个音频文件回写元数据，%d/%d 个嵌入封面",
            task.id, ok_meta, len(audio_files), ok_cover, len(audio_files),
        )

    if cover_bytes and ok_cover == 0:
        try:
            cover_path = target_base / "cover.jpg"
            cover_path.write_bytes(cover_bytes)
            logger.warning("任务 %s: 嵌入封面全部失败，已回退保存 cover.jpg 到 %s", task.id, cover_path)
        except Exception as e:
            logger.warning("任务 %s: 保存 cover.jpg 失败: %s", task.id, e)

    if cover_bytes:
        task.cover_applied = True
        db.commit()


def _worker(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.get(BiliDownloadTask, task_id)
        if task is None:
            return

        task.status = "running"
        task.updated_at = datetime.utcnow()
        db.commit()

        files: list[dict] = task.files_json or []
        selected: set[str] = set(task.selected_paths or [])
        if selected:
            files = [f for f in files if f.get("path") in selected]

        task.total_files = len(files)
        db.commit()

        watch_dir_path = _get_watch_dir_path(task.target_watch_dir_id)
        if not watch_dir_path:
            task.status = "failed"
            task.error_message = f"watch_dir {task.target_watch_dir_id} 不存在"
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        from eta_bili.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        cookie = settings.get("bili_cookie") or ""
        client = BiliClient(cookie=cookie)

        completed = 0
        skipped = 0
        failed = 0
        errors: list[str] = []

        for f in files:
            db.refresh(task)
            if task.status == "canceled":
                return

            file_path = f.get("path", "")
            url = f.get("url")
            file_size = int(f.get("size") or 0)

            task.current_file = file_path
            task.current_file_size = file_size
            task.current_file_done = 0
            task.updated_at = datetime.utcnow()
            db.commit()

            if not url:
                failed += 1
                errors.append(f"{file_path}: 无下载链接")
                continue

            target = _build_target_path(
                watch_dir_path=watch_dir_path,
                subdir=task.target_subdir,
                title=task.title,
                file_rel_path=file_path,
            )

            if target.exists() and file_size > 0 and target.stat().st_size == file_size:
                skipped += 1
                continue

            try:
                def on_progress(done: int, total: int) -> None:
                    task.current_file_done = done

                downloaded = _download_one(client, url, target, on_progress=on_progress)
                completed += 1
            except Exception as e:
                failed += 1
                errors.append(f"{file_path}: {e}")
                logger.warning("下载失败 %s: %s", file_path, e)

            task.completed_files = completed
            task.skipped_files = skipped
            task.failed_files = failed
            task.updated_at = datetime.utcnow()
            db.commit()

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

        if completed > 0 or skipped > 0:
            _apply_metadata_and_cover(db, task, client)
            _create_album_playlist(db, task)

        if completed > 0 or skipped > 0:
            _trigger_local_node_scan()

    except Exception as e:
        logger.error("下载任务 %s 异常: %s", task_id, e, exc_info=True)
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
