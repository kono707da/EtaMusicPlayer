"""下载器：后台线程流式下载到节点 watch_dir

支持两种节点类型：
- 本地节点（local_node）：同进程直调，文件直接写入 watch_dir
- 远程节点（remote:name）：通过 HTTP API 推送，先下载到缓存池再上传

远程节点工作流程：
1. 下载文件到本地缓存池 data/cache_pool/{task_id}/
2. 应用元数据/封面到缓存文件
3. 通过 HTTP 上传到远程节点的 watch_dir
4. 清理缓存池
5. 触发远程节点扫描入库

缓存池大小可在设置页配置，超过限制时暂停下载等待上传完成。
"""
from __future__ import annotations

import logging
import os
import re
import shutil
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

try:
    from eta_shared.node_client import (
        LocalNodeClient,
        RemoteNodeClient,
        NodeClient,
        _build_target_path,
        create_node_client,
    )
except ImportError:
    create_node_client = None
    NodeClient = None
    LocalNodeClient = None
    RemoteNodeClient = None
    _build_target_path = None

logger = logging.getLogger("etamusic.plugins.bili_audio")

_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')

_CACHE_POOL_BASE = Path(__file__).resolve().parent.parent.parent / "data" / "cache_pool"

_AUDIO_EXTS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".ape"}


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _get_cache_dir(task_id: int) -> Path:
    d = _CACHE_POOL_BASE / str(task_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _clean_cache_dir(task_id: int) -> None:
    d = _CACHE_POOL_BASE / str(task_id)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def _cache_pool_size_mb() -> float:
    if not _CACHE_POOL_BASE.exists():
        return 0.0
    total = 0
    for f in _CACHE_POOL_BASE.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total / (1024 * 1024)


def _get_remote_nodes_config() -> list[dict]:
    """从访问端数据库获取远程节点配置"""
    try:
        from eta_web.plugins_manager.database import SessionLocal as WebSession
        from eta_web.plugins_manager.routers import _get_remote_nodes_config as _get
    except ImportError:
        return []
    db = WebSession()
    try:
        return _get(db)
    finally:
        db.close()


def _create_node_client_for_task(task: BiliDownloadTask):
    """根据任务的目标节点创建 NodeClient"""
    if create_node_client is None:
        logger.error("eta_shared.node_client 未安装")
        return None

    node_id = task.target_base_url
    remote_config = _get_remote_nodes_config() if node_id.startswith("remote:") else None
    return create_node_client(node_id, remote_config)


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
    with open(tmp, "wb") as f, client.stream_download(url) as resp:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            done += len(chunk)
            if on_progress:
                on_progress(done, total)
    os.replace(tmp, target)
    return done


def _apply_metadata_and_cover(
    db: Session,
    task: BiliDownloadTask,
    client: BiliClient,
    base_dir: Path,
) -> None:
    """下载完成后：把专辑/艺术家等元数据与封面回写到音频文件标签。

    base_dir 为音频文件所在目录（本地 watch_dir 子目录或远程缓存目录）。
    """
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

    if not base_dir.exists():
        return

    audio_files = [f for f in base_dir.rglob("*") if f.is_file() and f.suffix.lower() in _AUDIO_EXTS]

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
            cover_path = base_dir / "cover.jpg"
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

        from eta_bili.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        cookie = settings.get("bili_cookie") or ""
        cache_pool_limit_mb = float(settings.get("cache_pool_size_mb", "500"))
        client = BiliClient(cookie=cookie)

        # 创建节点客户端
        node_client = _create_node_client_for_task(task)
        if node_client is None:
            task.status = "failed"
            task.error_message = f"无法创建节点客户端: {task.target_base_url}"
            task.finished_at = datetime.utcnow()
            db.commit()
            return

        is_remote = not node_client.is_local
        cache_dir = _get_cache_dir(task_id) if is_remote else None

        # 获取 watch_dir 路径（本地节点需要，远程节点不需要）
        watch_dir_path = None
        if node_client.is_local:
            watch_dir_path = node_client.get_watch_dir_path(task.target_watch_dir_id)
            if not watch_dir_path:
                task.status = "failed"
                task.error_message = f"watch_dir {task.target_watch_dir_id} 不存在"
                task.finished_at = datetime.utcnow()
                db.commit()
                return

        completed = 0
        skipped = 0
        failed = 0
        errors: list[str] = []
        saved_paths: list[str] = []

        for idx, f in enumerate(files):
            db.refresh(task)
            if task.status == "canceled":
                _clean_cache_dir(task_id)
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

            # 检查缓存池大小（远程节点）
            if is_remote and cache_dir and idx > 0:
                current_size = _cache_pool_size_mb()
                if current_size > cache_pool_limit_mb:
                    logger.info(
                        "任务 %s: 缓存池 %.1fMB 超过限制 %.0fMB，暂停下载等待上传",
                        task_id, current_size, cache_pool_limit_mb,
                    )
                    _upload_cached_files(task, node_client, cache_dir)
                    _clean_uploaded_cache(task_id, cache_dir)

            # 构建目标路径
            if is_remote and cache_dir:
                # 远程节点：下载到缓存池
                download_target = _build_target_path(
                    watch_dir_path=str(cache_dir),
                    subdir="",
                    work_title=task.title,
                    file_rel_path=file_path,
                )
            else:
                # 本地节点：直接下载到 watch_dir
                download_target = _build_target_path(
                    watch_dir_path=watch_dir_path,
                    subdir=task.target_subdir,
                    work_title=task.title,
                    file_rel_path=file_path,
                )

            # 秒传判断
            if download_target.exists() and file_size > 0 and download_target.stat().st_size == file_size:
                skipped += 1
                saved_paths.append(str(download_target))
                continue

            try:
                def on_progress(done: int, total: int) -> None:
                    task.current_file_done = done

                downloaded = _download_one(client, url, download_target, on_progress=on_progress)
                completed += 1
                saved_paths.append(str(download_target))
            except Exception as e:
                failed += 1
                errors.append(f"{file_path}: {e}")
                logger.warning("下载失败 %s: %s", file_path, e)

            task.completed_files = completed
            task.skipped_files = skipped
            task.failed_files = failed
            task.updated_at = datetime.utcnow()
            db.commit()

        # 汇总状态
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
            # 计算元数据回写的 base_dir
            if is_remote and cache_dir:
                base_dir = cache_dir / _sanitize(task.title)
            else:
                base_dir = Path(watch_dir_path)
                if task.target_subdir:
                    base_dir = base_dir / task.target_subdir.strip("/\\")
                base_dir = base_dir / _sanitize(task.title)

            _apply_metadata_and_cover(db, task, client, base_dir)

            if is_remote and cache_dir:
                # 远程节点：上传所有文件到远程节点，获取远程路径
                remote_paths = _upload_all_to_remote(task, node_client, cache_dir)
                _clean_cache_dir(task_id)
                # 用远程节点上的路径替换本地缓存路径
                saved_paths = remote_paths

            # 触发扫描
            node_client.trigger_scan()

            # 添加到收集箱（本地和远程节点均支持）
            try:
                audio_paths = [
                    p for p in saved_paths
                    if Path(p).suffix.lower() in _AUDIO_EXTS
                ]
                if audio_paths:
                    track_ids = node_client.find_tracks_by_paths(audio_paths)
                    if track_ids:
                        added = node_client.add_tracks_to_inbox(track_ids)
                        if added > 0:
                            logger.info("已将 %d 首曲目添加到收集箱", added)
            except Exception as e:
                logger.warning("添加到收集箱失败: %s", e)

    except Exception as e:
        logger.error("下载任务 %s 异常: %s", task_id, e, exc_info=True)
        _clean_cache_dir(task_id)
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


def _upload_cached_files(
    task: BiliDownloadTask,
    node_client,
    cache_dir: Path,
) -> None:
    """上传缓存目录中已完成的文件到远程节点（缓存池满时调用）"""
    work_dir_name = _sanitize(task.title)
    cache_work_dir = cache_dir / work_dir_name
    if not cache_work_dir.exists():
        return
    for f in list(cache_work_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix == ".part":
            continue
        try:
            rel = f.relative_to(cache_dir)
            parts = list(rel.parts)
            if parts and parts[0] == work_dir_name:
                parts = parts[1:]
            file_rel = "/".join(parts)
            node_client.save_file(
                watch_dir_id=task.target_watch_dir_id,
                subdir=task.target_subdir or "",
                work_title=task.title,
                file_rel_path=file_rel,
                source_path=f,
            )
            f.unlink(missing_ok=True)
            logger.info("任务 %s: 已上传 %s 到远程节点", task.id, file_rel)
        except Exception as e:
            logger.warning("任务 %s: 上传文件失败 %s: %s", task.id, f, e)


def _clean_uploaded_cache(task_id: int, cache_dir: Path) -> None:
    """清理已上传的缓存文件（bili 无 DownloadFileStatus，文件在上传时已删除）"""
    pass


def _upload_all_to_remote(
    task: BiliDownloadTask,
    node_client,
    cache_dir: Path,
) -> list[str]:
    """上传所有缓存文件到远程节点，返回远程节点上的绝对路径列表"""
    remote_paths: list[str] = []
    work_dir_name = _sanitize(task.title)
    cache_work_dir = cache_dir / work_dir_name
    if not cache_work_dir.exists():
        return remote_paths
    for f in list(cache_work_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix == ".part":
            continue
        try:
            rel = f.relative_to(cache_dir)
            parts = list(rel.parts)
            if parts and parts[0] == work_dir_name:
                parts = parts[1:]
            file_rel = "/".join(parts)
            saved_to = node_client.save_file(
                watch_dir_id=task.target_watch_dir_id,
                subdir=task.target_subdir or "",
                work_title=task.title,
                file_rel_path=file_rel,
                source_path=f,
            )
            if saved_to:
                remote_paths.append(saved_to)
            f.unlink(missing_ok=True)
            logger.info("任务 %s: 已上传 %s 到远程节点", task.id, file_rel)
        except Exception as e:
            logger.warning("任务 %s: 上传文件失败 %s: %s", task.id, f, e)
    return remote_paths


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
