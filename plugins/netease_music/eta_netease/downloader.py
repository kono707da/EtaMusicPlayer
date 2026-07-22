"""网易云下载器：后台线程下载歌曲到节点 watch_dir

流程：
1. 获取下载 URL（song_download_url API）
2. 下载文件
3. 如果是 ncm 格式 → 解密
4. 写入元数据/封面
5. 触发节点扫描
6. 添加到收集箱

支持本地节点和远程节点（通过 eta_shared.node_client）。
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy.orm import Session

from eta_netease.api_search import song_detail, song_download_url
from eta_netease.database import SessionLocal
from eta_netease.models import DownloadFileStatus, DownloadTask
from eta_netease.ncm_decrypt import NcmError, decrypt_ncm

try:
    from eta_shared.tag_writer import (
        AUDIO_EXTS,
        write_lyrics_to_file,
        write_tags_and_cover,
    )
except ImportError:
    AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".alac", ".aac", ".wav"}
    write_tags_and_cover = None
    write_lyrics_to_file = None

try:
    from eta_shared.node_client import (
        LocalNodeClient,
        NodeClient,
        RemoteNodeClient,
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

logger = logging.getLogger("etamusic.plugins.netease")

_lock = threading.Lock()
_running_tasks: dict[int, threading.Thread] = {}

_CACHE_POOL_BASE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "cache_pool"


def _get_cache_dir(task_id: int) -> Path:
    d = _CACHE_POOL_BASE / str(task_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _clean_cache_dir(task_id: int) -> None:
    d = _CACHE_POOL_BASE / str(task_id)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitize_filename(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _build_song_filename(song: dict, fmt: str) -> str:
    """构建歌曲文件名: Artist - Title.ext"""
    name = song.get("name", "unknown")
    artist = song.get("artist", "")
    if artist:
        filename = f"{artist} - {name}"
    else:
        filename = name
    filename = _sanitize_filename(filename)
    return f"{filename}.{fmt}"


def _get_song_detail(song_id: int) -> dict:
    """获取歌曲详情（名称、艺术家等）"""
    try:
        resp = song_detail([song_id])
        songs = resp.get("songs", [])
        if songs:
            s = songs[0]
            artists = s.get("ar", []) or s.get("artists", [])
            artist_str = " / ".join(a.get("name", "") for a in artists if a.get("name"))
            return {
                "song_id": song_id,
                "name": s.get("name", ""),
                "artist": artist_str,
                "album": (s.get("al", {}) or {}).get("name", ""),
                "album_pic": (s.get("al", {}) or {}).get("picUrl", ""),
            }
    except Exception as e:
        logger.warning("获取歌曲详情失败 %s: %s", song_id, e)
    return {"song_id": song_id, "name": str(song_id), "artist": "", "album": ""}


def _download_url_to_file(
    url: str,
    target: Path,
    proxy: Optional[str] = None,
    on_progress=None,
) -> int:
    """下载 URL 到文件，返回下载字节数"""
    target.parent.mkdir(parents=True, exist_ok=True)

    proxies = {"http": proxy, "https": proxy} if proxy else None
    resp = requests.get(url, stream=True, timeout=60, proxies=proxies)
    resp.raise_for_status()

    total = int(resp.headers.get("Content-Length") or 0)
    done = 0
    tmp = target.with_suffix(target.suffix + ".part")
    with open(tmp, "wb") as f:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            f.write(chunk)
            done += len(chunk)
            if on_progress:
                on_progress(done, total)
    os.replace(tmp, target)
    return done


def _is_ncm_file(data: bytes) -> bool:
    """检查是否为 ncm 格式（魔数 CTENFDAM）"""
    return len(data) >= 8 and data[:8] == b"CTENFDAM"


def _process_downloaded_file(
    raw_path: Path,
    song: dict,
    target_dir: Path,
) -> tuple[Path, str, bool]:
    """处理下载的文件：如果是 ncm 则解密

    Returns:
        (最终文件路径, 格式, 是否解密)
    """
    raw_data = raw_path.read_bytes()

    if _is_ncm_file(raw_data):
        logger.info("检测到 ncm 格式，开始解密: %s", song.get("name", ""))
        result = decrypt_ncm(raw_data)

        fmt = result.fmt
        filename = _build_song_filename(song, fmt)
        target_path = target_dir / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(result.audio_data)

        # 删除原始 ncm 文件
        raw_path.unlink(missing_ok=True)

        # 写入元数据（ncm 解密后可能有封面字节）
        if write_tags_and_cover:
            cover = result.cover_data
            write_tags_and_cover(
                str(target_path),
                title=result.music_name or song.get("name"),
                artist=" & ".join(result.artists) if result.artists else song.get("artist"),
                album=result.album or song.get("album"),
                cover_bytes=cover,
            )

        return target_path, fmt, True
    else:
        # 非 ncm 文件，直接移动
        ext = raw_path.suffix.lower().lstrip(".")
        if not ext:
            ext = "mp3"
        filename = _build_song_filename(song, ext)
        target_path = target_dir / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if raw_path.resolve() != target_path.resolve():
            shutil.move(str(raw_path), str(target_path))

        # 写入基本元数据
        if write_tags_and_cover and target_path.suffix.lower() in AUDIO_EXTS:
            write_tags_and_cover(
                str(target_path),
                title=song.get("name"),
                artist=song.get("artist"),
                album=song.get("album"),
            )

        return target_path, ext, False


def _get_remote_nodes_config() -> list[dict]:
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


def _create_node_client_for_task(task: DownloadTask):
    if create_node_client is None:
        logger.error("eta_shared.node_client 未安装")
        return None
    node_id = task.target_base_url
    remote_config = _get_remote_nodes_config() if node_id.startswith("remote:") else None
    return create_node_client(node_id, remote_config)


def _worker(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.get(DownloadTask, task_id)
        if task is None:
            return

        task.status = "running"
        task.updated_at = datetime.utcnow()
        db.commit()

        songs: list[dict] = task.songs_json or []
        selected_ids = set(task.selected_song_ids or [])
        if selected_ids:
            songs = [s for s in songs if str(s.get("song_id", "")) in selected_ids or s.get("song_id") in selected_ids]

        # 补全歌曲详情
        for song in songs:
            if not song.get("name"):
                detail = _get_song_detail(int(song["song_id"]))
                song["name"] = detail["name"]
                song["artist"] = detail.get("artist", "")
                song["album"] = detail.get("album", "")

        task.total_files = len(songs)
        db.commit()

        # 清理旧状态
        db.query(DownloadFileStatus).filter(DownloadFileStatus.task_id == task_id).delete()
        db.commit()

        for song in songs:
            db.add(
                DownloadFileStatus(
                    task_id=task_id,
                    song_id=int(song.get("song_id", 0)),
                    file_path=song.get("name", ""),
                    status="pending",
                    size=int(song.get("size") or 0),
                    done=0,
                )
            )
        db.commit()

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

        # 获取 watch_dir 路径（本地节点）
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

        for song in songs:
            db.refresh(task)
            if task.status == "canceled":
                _clean_cache_dir(task_id)
                return

            song_id = int(song.get("song_id", 0))
            song_name = song.get("name", str(song_id))

            file_status = (
                db.query(DownloadFileStatus)
                .filter(
                    DownloadFileStatus.task_id == task_id,
                    DownloadFileStatus.song_id == song_id,
                )
                .one_or_none()
            )

            task.current_file = song_name
            task.current_file_size = int(song.get("size") or 0)
            task.current_file_done = 0
            task.updated_at = datetime.utcnow()
            if file_status:
                file_status.status = "downloading"
                file_status.updated_at = datetime.utcnow()
            db.commit()

            try:
                # 获取下载 URL
                level = task.level or "exhigh"
                dl_resp = song_download_url(song_id, level=level)
                dl_data = dl_resp.get("data", {})
                url = dl_data.get("url")
                file_size = int(dl_data.get("size") or 0)
                file_type = dl_data.get("type", "").lower()

                if not url:
                    failed += 1
                    if file_status:
                        file_status.status = "failed"
                        file_status.error = "无下载链接（可能需要 VIP）"
                    errors.append(f"{song_name}: 无下载链接")
                    continue

                if file_status:
                    file_status.size = file_size
                task.current_file_size = file_size
                db.commit()

                # 下载到临时文件
                raw_dir = cache_dir or Path(watch_dir_path)
                raw_tmp = raw_dir / f".{task_id}_{song_id}.ncm" if file_type == "ncm" else raw_dir / f".{task_id}_{song_id}.{file_type}"

                # 远程节点下载到 cache_dir，本地节点直接下载到 watch_dir 的临时文件
                if is_remote and cache_dir:
                    download_target = cache_dir / f"{task_id}_{song_id}_raw"
                else:
                    download_target = raw_tmp

                def on_progress(done: int, total: int) -> None:
                    task.current_file_done = done
                    if file_status:
                        file_status.done = done

                downloaded = _download_url_to_file(url, download_target, on_progress=on_progress)
                completed += 1

                if file_status:
                    file_status.status = "decrypting" if file_type == "ncm" else "completed"
                    file_status.done = downloaded
                    file_status.was_ncm = file_type == "ncm"
                    db.commit()

                # 处理文件（解密 + 移动到目标位置）
                if is_remote and cache_dir:
                    # 远程节点：在 cache_dir 中处理
                    target_subdir_path = cache_dir / (task.target_subdir or "")
                    final_path, fmt, was_ncm = _process_downloaded_file(
                        download_target, song, target_subdir_path
                    )
                    # 上传到远程节点
                    try:
                        work_title = task.source_title or "netease"
                        saved_to = node_client.save_file(
                            watch_dir_id=task.target_watch_dir_id,
                            subdir=task.target_subdir or "",
                            work_title=work_title,
                            file_rel_path=final_path.name,
                            source_path=final_path,
                        )
                        if file_status:
                            file_status.saved_to = saved_to
                            file_status.status = "completed"
                            file_status.decrypted_format = fmt
                        final_path.unlink(missing_ok=True)
                    except Exception as e:
                        failed += 1
                        completed -= 1
                        if file_status:
                            file_status.status = "failed"
                            file_status.error = f"上传失败: {e}"
                        errors.append(f"{song_name}: 上传失败: {e}")
                else:
                    # 本地节点：直接处理到 watch_dir
                    work_title = task.source_title or "netease"
                    target_dir = Path(watch_dir_path)
                    if task.target_subdir:
                        target_dir = target_dir / task.target_subdir
                    target_dir = target_dir / _sanitize_filename(work_title)
                    target_dir.mkdir(parents=True, exist_ok=True)

                    final_path, fmt, was_ncm = _process_downloaded_file(
                        download_target, song, target_dir
                    )
                    if file_status:
                        file_status.saved_to = str(final_path)
                        file_status.status = "completed"
                        file_status.decrypted_format = fmt

            except NcmError as e:
                failed += 1
                if file_status:
                    file_status.status = "failed"
                    file_status.error = f"ncm解密失败: {e}"
                errors.append(f"{song_name}: ncm解密失败: {e}")
                logger.warning("ncm 解密失败 %s: %s", song_name, e)
            except Exception as e:
                failed += 1
                if file_status:
                    file_status.status = "failed"
                    file_status.error = str(e)[:500]
                errors.append(f"{song_name}: {e}")
                logger.warning("下载失败 %s: %s", song_name, e, exc_info=True)

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
            # 远程节点清理
            if is_remote and cache_dir:
                _clean_cache_dir(task_id)

            # 触发扫描
            try:
                node_client.trigger_scan()
            except Exception as e:
                logger.warning("触发扫描失败: %s", e)

            # 添加到收集箱
            try:
                file_statuses = (
                    db.query(DownloadFileStatus)
                    .filter(
                        DownloadFileStatus.task_id == task.id,
                        DownloadFileStatus.status == "completed",
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
