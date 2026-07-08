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
from app.utils.tag_writer import (
    AUDIO_EXTS,
    vtt_to_lrc,
    write_lyrics_to_file,
    write_tags_and_cover,
)

logger = logging.getLogger("etamusic.plugins.asmr_one")

_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _build_target_path(
    watch_dir_path: str,
    subdir: Optional[str],
    work_title: str,
    file_rel_path: str,
) -> Path:
    parts = [watch_dir_path]
    if subdir:
        parts.append(subdir.strip("/\\"))
    parts.append(_sanitize(work_title))
    for seg in file_rel_path.split("/"):
        if seg:
            parts.append(_sanitize(seg))
    return Path(*parts)


def _get_watch_dir_path(watch_dir_id: int) -> Optional[str]:
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


def _create_album_playlist(db: Session, task: DownloadTask) -> Optional[int]:
    try:
        from app.plugins.local_node.database import SessionLocal as LocalSession
        from app.plugins.local_node.models import Playlist, PlaylistItem, Track, User
    except ImportError as e:
        logger.warning("无法导入 local_node 模块: %s", e)
        return None

    db_local = LocalSession()
    try:
        file_statuses = (
            db.query(DownloadFileStatus)
            .filter(
                DownloadFileStatus.task_id == task.id,
                DownloadFileStatus.status.in_(["completed", "skipped"]),
                DownloadFileStatus.saved_to.isnot(None),
            )
            .all()
        )
        audio_files = [
            fs for fs in file_statuses
            if fs.saved_to and Path(fs.saved_to).suffix.lower() in AUDIO_EXTS
        ]
        if not audio_files:
            logger.info("任务 %s: 无音频文件，跳过创建播放列表", task.id)
            return None

        saved_paths = [fs.saved_to for fs in audio_files]
        tracks = (
            db_local.query(Track)
            .filter(Track.abs_path.in_(saved_paths))
            .all()
        )
        if not tracks:
            logger.warning(
                "任务 %s: 未在 local_node 找到对应 Track（可能扫描未完成），跳过播放列表创建",
                task.id,
            )
            return None

        admin = db_local.query(User).filter(User.is_admin.is_(True)).first()
        if admin is None:
            logger.warning("任务 %s: local_node 无 admin 用户，跳过播放列表创建", task.id)
            return None

        playlist_name = task.work_title or f"ASMR {task.work_id}"
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
                description=f"asmr.one work_id={task.work_id}",
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
    client: AsmrClient,
    url: str,
    target: Path,
    on_progress=None,
) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    try:
        headers = client.head(url)
        total = int(headers.get("Content-Length") or 0)
    except Exception:
        pass

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


def _apply_metadata_and_cover(
    db: Session,
    task: DownloadTask,
    client: AsmrClient,
    cover_mode: str = "embed",
) -> None:
    """下载完成后：把专辑/艺术家等元数据与封面回写到音频文件标签。

    metadata_json 结构：
      {album, artist, album_artist, source_url, cover_type}
    cover_type 取值：main / sam / 240x240，None 表示不写封面

    cover_mode 取值：
      - "embed": 仅嵌入到音频文件标签
      - "save":  仅保存为 cover.jpg 到下载目录
      - "both":  嵌入 + 保存 cover.jpg
    """
    meta = task.metadata_json or {}
    if not meta:
        return

    album = meta.get("album")
    artist = meta.get("artist")
    album_artist = meta.get("album_artist")
    source_url = meta.get("source_url")
    cover_type = meta.get("cover_type")

    has_meta = any(v for v in (album, artist, album_artist, source_url))

    file_statuses = (
        db.query(DownloadFileStatus)
        .filter(
            DownloadFileStatus.task_id == task.id,
            DownloadFileStatus.status.in_(["completed", "skipped"]),
            DownloadFileStatus.saved_to.isnot(None),
        )
        .all()
    )

    audio_files = [
        fs for fs in file_statuses
        if fs.saved_to and Path(fs.saved_to).suffix.lower() in AUDIO_EXTS
    ]

    if not audio_files:
        return

    need_cover = bool(cover_type) and not task.cover_applied
    cover_bytes = None
    cover_mime = "image/jpeg"
    if need_cover:
        try:
            cover_bytes = client.get_cover_bytes(task.work_id, cover_type=cover_type)
        except Exception as e:
            logger.warning("任务 %s: 获取封面字节失败: %s", task.id, e)
            need_cover = False

    do_embed = cover_mode in ("embed", "both") and need_cover
    do_save = cover_mode in ("save", "both") and need_cover

    ok_cover = 0
    ok_meta = 0
    if do_embed or (has_meta and cover_mode != "save"):
        for fs in audio_files:
            try:
                success = write_tags_and_cover(
                    fs.saved_to,
                    title=None,
                    artist=artist,
                    album=album,
                    album_artist=album_artist,
                    source_url=source_url,
                    cover_bytes=cover_bytes if do_embed else None,
                    cover_mime=cover_mime,
                )
                if success:
                    ok_meta += 1
                    if do_embed:
                        ok_cover += 1
            except Exception as e:
                logger.warning("回写标签/封面失败 %s: %s", fs.saved_to, e)
        logger.info(
            "任务 %s: 已为 %d/%d 个音频文件回写元数据，%d/%d 个嵌入封面",
            task.id, ok_meta, len(audio_files), ok_cover, len(audio_files),
        )

    should_save = do_save or (do_embed and ok_cover == 0 and cover_bytes)
    if should_save:
        try:
            first_dir = Path(audio_files[0].saved_to).parent
            cover_path = first_dir / "cover.jpg"
            cover_path.write_bytes(cover_bytes)
            if do_embed and ok_cover == 0:
                logger.warning(
                    "任务 %s: 嵌入封面全部失败，已回退保存 cover.jpg 到 %s",
                    task.id, cover_path,
                )
            else:
                logger.info("任务 %s: 封面已保存到 %s", task.id, cover_path)
        except Exception as e:
            logger.warning("任务 %s: 保存 cover.jpg 失败: %s", task.id, e)

    if need_cover:
        task.cover_applied = True
        db.commit()


def _apply_lyrics_from_vtt(
    db: Session,
    task: DownloadTask,
    client: AsmrClient,
) -> None:
    """下载完成后：把 VTT 字幕转换为 LRC 并嵌入音频文件歌词标签。"""
    files_json = task.files_json or []
    vtt_files = [f for f in files_json if f.get("path", "").lower().endswith(".vtt")]
    if not vtt_files:
        return

    file_statuses = (
        db.query(DownloadFileStatus)
        .filter(
            DownloadFileStatus.task_id == task.id,
            DownloadFileStatus.status.in_(["completed", "skipped"]),
            DownloadFileStatus.saved_to.isnot(None),
        )
        .all()
    )
    audio_files = [
        fs for fs in file_statuses
        if fs.saved_to and Path(fs.saved_to).suffix.lower() in AUDIO_EXTS
    ]
    if not audio_files:
        return

    for vtt_file in vtt_files:
        vtt_path = vtt_file.get("path", "")
        vtt_name = Path(vtt_path).stem
        try:
            vtt_url = vtt_file.get("url")
            if not vtt_url:
                continue
            resp = client.session.get(vtt_url, timeout=30)
            resp.raise_for_status()
            vtt_content = resp.text
            lrc_text = vtt_to_lrc(vtt_content)
            if not lrc_text:
                continue
        except Exception as e:
            logger.warning("任务 %s: 下载 VTT 失败 %s: %s", task.id, vtt_path, e)
            continue

        matched = [
            fs for fs in audio_files
            if Path(fs.saved_to).stem == vtt_name
        ]
        if not matched:
            matched = audio_files[:1]

        for fs in matched:
            try:
                if write_lyrics_to_file(fs.saved_to, lrc_text):
                    logger.info("任务 %s: 已写入歌词到 %s", task.id, fs.saved_to)
            except Exception as e:
                logger.warning("任务 %s: 写入歌词失败 %s: %s", task.id, fs.saved_to, e)


def _worker(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.get(DownloadTask, task_id)
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

        from app.plugins.asmr_one.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        proxy = settings.get("proxy_url") or "http://127.0.0.1:7897"
        client = AsmrClient(proxy_url=proxy)

        completed = 0
        skipped = 0
        failed = 0
        errors: list[str] = []

        db.query(DownloadFileStatus).filter(DownloadFileStatus.task_id == task_id).delete()
        db.commit()

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
            _apply_lyrics_from_vtt(db, task, client)
            _create_album_playlist(db, task)

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
    with _lock:
        if task_id in _running_tasks:
            return
        t = threading.Thread(target=_worker, args=(task_id,), daemon=True)
        _running_tasks[task_id] = t
        t.start()


def cancel_download_task(task_id: int) -> bool:
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
