"""下载器：后台线程流式下载到节点 watch_dir

支持两种节点类型：
- 本地节点（local_node）：同进程直调，文件直接写入 watch_dir
- 远程节点（remote:name）：通过 HTTP API 推送，先下载到缓存池再上传

远程节点工作流程：
1. 下载文件到本地缓存池 data/cache_pool/{task_id}/
2. 应用元数据/封面/歌词到缓存文件
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

from eta_asmr.asmr_client import AsmrClient
from eta_asmr.database import SessionLocal
from eta_asmr.models import DownloadFileStatus, DownloadTask

try:
    from eta_shared.tag_writer import (
        AUDIO_EXTS,
        vtt_to_lrc,
        write_lyrics_to_file,
        write_tags_and_cover,
    )
except ImportError:
    AUDIO_EXTS = set()
    vtt_to_lrc = None
    write_lyrics_to_file = None
    write_tags_and_cover = None

try:
    from eta_shared.node_client import (
        LocalNodeClient,
        RemoteNodeClient,
        NodeClient,
        _build_target_path,
        _sanitize,
        create_node_client,
    )
except ImportError:
    create_node_client = None
    NodeClient = None
    LocalNodeClient = None
    RemoteNodeClient = None
    _build_target_path = None
    _sanitize = None

logger = logging.getLogger("etamusic.plugins.asmr_one")

_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}

_CACHE_POOL_BASE = Path(__file__).resolve().parent.parent.parent / "data" / "cache_pool"


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
    """下载完成后：把专辑/艺术家等元数据与封面回写到音频文件标签。"""
    if write_tags_and_cover is None:
        logger.warning("eta_shared 未安装，跳过元数据/封面回写")
        return

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
    if vtt_to_lrc is None or write_lyrics_to_file is None:
        logger.warning("eta_shared 未安装，跳过歌词写入")
        return

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


def _create_node_client_for_task(task: DownloadTask, verify_ssl: bool = True):
    """根据任务的目标节点创建 NodeClient"""
    if create_node_client is None:
        logger.error("eta_shared.node_client 未安装")
        return None

    node_id = task.target_base_url
    remote_config = _get_remote_nodes_config() if node_id.startswith("remote:") else None
    return create_node_client(node_id, remote_config, verify_ssl=verify_ssl)


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

        from eta_asmr.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        proxy = settings.get("proxy_url") or None
        verify_ssl = settings.get("verify_ssl", "true").lower() not in ("false", "0", "no")
        cache_pool_limit_mb = float(settings.get("cache_pool_size_mb", "500"))
        client = AsmrClient(proxy_url=proxy, verify_ssl=verify_ssl)

        # 创建节点客户端
        node_client = _create_node_client_for_task(task, verify_ssl=verify_ssl)
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
                _clean_cache_dir(task_id)
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

            # 检查缓存池大小（远程节点）
            if is_remote and cache_dir and idx > 0:
                current_size = _cache_pool_size_mb()
                if current_size > cache_pool_limit_mb:
                    logger.info(
                        "任务 %s: 缓存池 %.1fMB 超过限制 %.0fMB，暂停下载等待上传",
                        task_id, current_size, cache_pool_limit_mb,
                    )
                    # 上传已完成的缓存文件以释放空间
                    _upload_cached_files(db, task, node_client, cache_dir)
                    # 清理已上传的缓存文件
                    _clean_uploaded_cache(db, task_id, cache_dir)

            # 构建目标路径
            if is_remote and cache_dir:
                # 远程节点：下载到缓存池
                download_target = _build_target_path(
                    watch_dir_path=str(cache_dir),
                    subdir="",
                    work_title=task.work_title,
                    file_rel_path=file_path,
                )
            else:
                # 本地节点：直接下载到 watch_dir
                download_target = _build_target_path(
                    watch_dir_path=watch_dir_path,
                    subdir=task.target_subdir,
                    work_title=task.work_title,
                    file_rel_path=file_path,
                )

            # 秒传判断
            if download_target.exists() and task.current_file_size > 0 and download_target.stat().st_size == task.current_file_size:
                skipped += 1
                if file_status:
                    file_status.status = "skipped"
                    file_status.done = task.current_file_size
                    file_status.saved_to = str(download_target)
                continue

            try:
                def on_progress(done: int, total: int) -> None:
                    task.current_file_done = done
                    if file_status:
                        file_status.done = done

                downloaded = _download_one(client, url, download_target, on_progress=on_progress)
                completed += 1
                if file_status:
                    file_status.status = "completed"
                    file_status.done = downloaded
                    file_status.saved_to = str(download_target)
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
            # 应用元数据/封面/歌词（对本地文件或缓存文件）
            _apply_metadata_and_cover(db, task, client)
            _apply_lyrics_from_vtt(db, task, client)

            if is_remote and cache_dir:
                # 远程节点：上传所有文件到远程节点
                _upload_all_to_remote(db, task, node_client, cache_dir)
                _clean_cache_dir(task_id)

            # 触发扫描
            node_client.trigger_scan()

            # 添加到收集箱（本地和远程节点均支持）
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
                saved_paths = [fs.saved_to for fs in file_statuses if fs.saved_to]
                if saved_paths:
                    track_ids = node_client.find_tracks_by_paths(saved_paths)
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


def _upload_cached_files(
    db: Session,
    task: DownloadTask,
    node_client,
    cache_dir: Path,
) -> None:
    """上传缓存目录中已完成的文件到远程节点"""
    file_statuses = (
        db.query(DownloadFileStatus)
        .filter(
            DownloadFileStatus.task_id == task.id,
            DownloadFileStatus.status == "completed",
            DownloadFileStatus.saved_to.isnot(None),
        )
        .all()
    )
    for fs in file_statuses:
        if not fs.saved_to:
            continue
        local_path = Path(fs.saved_to)
        if not local_path.exists():
            continue
        # 只上传缓存目录中的文件
        try:
            if cache_dir not in local_path.parents and local_path != cache_dir:
                continue
        except TypeError:
            continue
        try:
            file_rel = str(local_path.relative_to(cache_dir / _sanitize(task.work_title)))
            saved_to = node_client.save_file(
                watch_dir_id=task.target_watch_dir_id,
                subdir=task.target_subdir or "",
                work_title=task.work_title,
                file_rel_path=file_rel,
                source_path=local_path,
            )
            # 更新 saved_to 为远程节点上的路径
            fs.saved_to = saved_to
            db.commit()
            local_path.unlink(missing_ok=True)
            logger.info("任务 %s: 已上传 %s 到远程节点", task.id, file_rel)
        except Exception as e:
            logger.warning("任务 %s: 上传文件失败 %s: %s", task.id, local_path, e)


def _clean_uploaded_cache(
    db: Session,
    task_id: int,
    cache_dir: Path,
) -> None:
    """清理已上传的缓存文件（saved_to 已不在缓存目录中的）"""
    file_statuses = (
        db.query(DownloadFileStatus)
        .filter(
            DownloadFileStatus.task_id == task_id,
            DownloadFileStatus.status == "completed",
            DownloadFileStatus.saved_to.isnot(None),
        )
        .all()
    )
    for fs in file_statuses:
        if not fs.saved_to:
            continue
        local_path = Path(fs.saved_to)
        # 如果 saved_to 不在缓存目录中，说明已上传
        try:
            if cache_dir not in local_path.parents and local_path != cache_dir:
                continue
        except TypeError:
            continue


def _upload_all_to_remote(
    db: Session,
    task: DownloadTask,
    node_client,
    cache_dir: Path,
) -> None:
    """上传所有缓存文件到远程节点"""
    file_statuses = (
        db.query(DownloadFileStatus)
        .filter(
            DownloadFileStatus.task_id == task.id,
            DownloadFileStatus.status.in_(["completed", "skipped"]),
            DownloadFileStatus.saved_to.isnot(None),
        )
        .all()
    )

    work_dir_name = _sanitize(task.work_title)
    for fs in file_statuses:
        if not fs.saved_to:
            continue
        local_path = Path(fs.saved_to)

        # 如果 saved_to 已经不在缓存目录中，说明已经上传过（缓存池满时提前上传）
        try:
            is_in_cache = cache_dir in local_path.parents or local_path == cache_dir
        except TypeError:
            is_in_cache = False

        if not is_in_cache:
            # 已上传，跳过
            continue

        if not local_path.exists():
            logger.warning("任务 %s: 缓存文件不存在 %s", task.id, local_path)
            continue

        try:
            # 计算相对路径（去掉 work_title 前缀）
            rel = local_path.relative_to(cache_dir)
            parts = list(rel.parts)
            if parts and parts[0] == work_dir_name:
                parts = parts[1:]
            file_rel = "/".join(parts)

            saved_to = node_client.save_file(
                watch_dir_id=task.target_watch_dir_id,
                subdir=task.target_subdir or "",
                work_title=task.work_title,
                file_rel_path=file_rel,
                source_path=local_path,
            )
            fs.saved_to = saved_to
            db.commit()
            local_path.unlink(missing_ok=True)
            logger.info("任务 %s: 已上传 %s 到远程节点", task.id, file_rel)
        except Exception as e:
            logger.warning("任务 %s: 上传文件失败 %s: %s", task.id, local_path, e)


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
