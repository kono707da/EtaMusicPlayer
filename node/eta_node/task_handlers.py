"""任务处理器注册

所有写操作的处理器在此注册到 TaskExecutor。
每个处理器签名: (db: Session, payload: dict | None, task: NodeTask) -> dict | None
处理器内部不需要 commit（由 TaskExecutor 统一 commit），但可以 flush。

例外：`_handle_track_delete` 必须自行显式 commit 以在数据库提交失败时
执行文件系统补偿事务（把已隔离的文件恢复到原路径）。详见需求书 8.2。
"""
from __future__ import annotations

import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from eta_node.models import NodeTask, Playlist, PlaylistItem, Track, TrackStats, WatchDir
from eta_node.m3u_importer import handle_import_m3u
from eta_node.scanner import scan_directory
from eta_node.task_executor import TaskExecutor, write_audit_log
from eta_node.versioning import (
    ENTITY_PLAYLISTS,
    ENTITY_TRACKS,
    bump_and_stamp,
)

logger = logging.getLogger("eta_node.task_handlers")


# ---- scan 处理器 ----

def _handle_scan(
    db: Session, payload: Optional[dict], task: NodeTask
) -> Optional[dict]:
    """扫描监控目录，将音频文件元数据入库

    payload:
        watch_dir_id: int | None  (None = 扫描所有启用的目录)

    1.2.1 起：调用 scan_directory(commit=False)，由 TaskExecutor._execute_task
    统一 commit，保证整个扫描任务的原子性。
    """
    watch_dir_id = payload.get("watch_dir_id") if payload else None

    query = db.query(WatchDir).filter(WatchDir.enabled.is_(True))
    if watch_dir_id is not None:
        query = query.filter(WatchDir.id == watch_dir_id)
    watch_dirs = query.all()

    if not watch_dirs:
        return {
            "total_files": 0,
            "new_tracks": 0,
            "updated_tracks": 0,
            "missing_tracks": 0,
            "restored_tracks": 0,
            "message": "no enabled watch_dirs",
        }

    total_all = 0
    new_all = 0
    updated_all = 0
    missing_all = 0
    restored_all = 0
    total_dirs = len(watch_dirs)

    for i, wd in enumerate(watch_dirs):
        # 1.2.1：commit=False，事务由 TaskExecutor 统一管理
        t, n, u, m, r = scan_directory(wd, db, commit=False)
        total_all += t
        new_all += n
        updated_all += u
        missing_all += m
        restored_all += r

        # 更新进度（flush，不 commit）
        task.progress = int((i + 1) / total_dirs * 100)
        db.flush()

    # 为新入库的 Track 创建 TrackStats
    if new_all > 0:
        _ensure_track_stats_for_recent(db, watch_dirs)

    # 审计日志
    write_audit_log(
        db,
        username=task.submitted_by,
        action="scan",
        target_type="watch_dir",
        target_id=watch_dir_id,
        detail={
            "total_files": total_all,
            "new_tracks": new_all,
            "updated_tracks": updated_all,
            "missing_tracks": missing_all,
            "restored_tracks": restored_all,
        },
        task_id=task.id,
    )

    return {
        "total_files": total_all,
        "new_tracks": new_all,
        "updated_tracks": updated_all,
        "missing_tracks": missing_all,
        "restored_tracks": restored_all,
    }


def _ensure_track_stats_for_recent(db: Session, watch_dirs: list[WatchDir]) -> None:
    """为缺少 TrackStats 的 Track 补充记录

    1.2.1：排除软删除曲目。
    """
    wd_ids = [wd.id for wd in watch_dirs]
    if not wd_ids:
        return

    from eta_node.models import Track
    from sqlalchemy import outerjoin, select

    # 找出没有 TrackStats 的 Track（排除软删除）
    tracks_without_stats = (
        db.query(Track)
        .filter(Track.watch_dir_id.in_(wd_ids), Track.deleted_at.is_(None))
        .filter(
            ~Track.id.in_(
                select(TrackStats.track_id)
            )
        )
        .all()
    )
    for track in tracks_without_stats:
        stats = TrackStats(track_id=track.id, imported_at=datetime.utcnow())
        db.add(stats)
    if tracks_without_stats:
        db.flush()


# ---- upload 处理器 ----

def _handle_upload(
    db: Session, payload: Optional[dict], task: NodeTask
) -> Optional[dict]:
    """将暂存文件移动到 watch_dir 目标位置

    payload:
        staging_path: str       暂存文件路径
        watch_dir_id: int       目标监控目录 ID
        subdir: str             子目录
        work_title: str         作品名（用作目录名）
        file_rel_path: str      文件相对路径
    """
    from eta_node.routers.upload import _build_target

    staging_path = payload.get("staging_path", "")
    watch_dir_id = payload.get("watch_dir_id")
    subdir = payload.get("subdir", "")
    work_title = payload.get("work_title", "")
    file_rel_path = payload.get("file_rel_path", "")

    wd = db.get(WatchDir, watch_dir_id)
    if wd is None:
        raise ValueError(f"监控目录不存在: {watch_dir_id}")

    src = Path(staging_path)
    if not src.exists():
        raise FileNotFoundError(f"暂存文件不存在: {staging_path}")

    target = _build_target(wd.path, subdir, work_title, file_rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # 原子移动
    shutil.move(str(src), str(target))

    logger.info("文件已移动: %s -> %s", staging_path, target)

    # 审计日志
    write_audit_log(
        db,
        username=task.submitted_by,
        action="upload",
        target_type="file",
        target_id=None,
        detail={"saved_to": str(target), "work_title": work_title},
        task_id=task.id,
    )

    return {"saved_to": str(target)}


# ---- track_delete 处理器 ----

# 隔离目录名（位于监控目录根下，与原文件相同文件系统，保证 os.rename 原子性）
TRASH_DIR_NAME = ".etamusic-trash"


def _resolve_inside_watch_dir(watch_dir_path: Path, target_path: Path) -> Path:
    """路径安全校验：确保 target 严格位于 watch_dir 内部且为普通文件。

    1.2.1 起强制（需求书 8.1）：
    - 不信任前端传入的任何路径，以数据库为准
    - 拒绝 .. 跨越、符号链接、junction、大小写差异
    - target 等于 watch_dir 根本身也拒绝
    - 目录一律拒绝

    校验失败抛 ValueError，由 _handle_track_delete 包装成业务异常。
    """
    # resolve() 会展开符号链接 / 处理 ..
    root = watch_dir_path.resolve(strict=True)
    target = target_path.resolve(strict=True)

    # 必须是普通文件
    if not target.is_file():
        raise ValueError("目标不是普通文件")

    # 严格位于根目录内部（target == root 会被拒绝）
    try:
        rel = target.relative_to(root)
    except ValueError:
        raise ValueError("文件路径越界")
    if rel == Path(""):
        raise ValueError("目标等于监控目录根本身")

    # 防御性二次校验：相对路径不能包含 .. 残留（resolve 后理论上不会，但保险）
    if ".." in rel.parts:
        raise ValueError("相对路径包含 .. 段")

    return target


def _handle_track_delete(
    db: Session, payload: Optional[dict], task: NodeTask
) -> Optional[dict]:
    """删除曲目文件 + 软删除数据库记录 + 清理引用（补偿事务）

    需求书第 7-8 章：
    - 路径越界防护（不信任前端路径）
    - 文件先原子重命名到隔离位置，再提交数据库事务
    - 数据库提交失败时把文件恢复原位
    - 数据库提交成功后永久删除隔离文件
    - 文件本已不存在时仅清理数据库，返回 file_missing=true
    - 软删除 Track.deleted_at + 删除所有 PlaylistItem + 版本戳 + 审计日志

    注意：本处理器内部显式 commit（违反通用约定），
    以便在数据库提交失败时执行文件系统补偿事务。

    payload:
        track_id: int
    """
    if not payload or "track_id" not in payload:
        raise ValueError("payload.track_id 缺失")
    track_id = int(payload["track_id"])

    track = db.get(Track, track_id)
    # 幂等保护：曲目不存在或已软删除时返回成功（说明上次已删除）
    if track is None:
        return {
            "track_id": track_id,
            "file_deleted": False,
            "file_missing": True,
            "removed_node_playlist_items": 0,
            "relative_path": None,
            "warning": "曲目不存在（可能已被删除）",
        }
    if track.deleted_at is not None:
        return {
            "track_id": track_id,
            "file_deleted": False,
            "file_missing": False,
            "removed_node_playlist_items": 0,
            "relative_path": track.rel_path,
            "warning": "曲目已软删除",
        }

    # 1. 重新读取监控目录 + 路径安全校验
    wd = db.get(WatchDir, track.watch_dir_id)
    if wd is None:
        raise ValueError(f"监控目录不存在: watch_dir_id={track.watch_dir_id}")

    try:
        watch_dir_path = Path(wd.path).resolve(strict=True)
    except (FileNotFoundError, OSError) as e:
        raise ValueError(f"监控目录不可访问: {wd.path} ({e})")

    track_abs = Path(track.abs_path)
    file_exists = track_abs.exists()

    # 文件存在 → 路径安全校验 + 原子重命名到隔离位置
    trash_path: Optional[Path] = None
    if file_exists:
        # 校验目标严格位于监控目录内且为普通文件
        try:
            resolved_target = _resolve_inside_watch_dir(watch_dir_path, track_abs)
        except ValueError as e:
            # 路径越界 / 目录 / 文件类型异常 → 任务失败，不修改任何状态
            raise ValueError(f"路径安全校验失败: {e}")

        # 准备隔离目录（与原文件相同文件系统，保证 os.rename 原子性）
        trash_dir = watch_dir_path / TRASH_DIR_NAME
        trash_dir.mkdir(parents=True, exist_ok=True)
        trash_path = trash_dir / f"{uuid.uuid4().hex}"
        try:
            os.rename(str(resolved_target), str(trash_path))
        except OSError as e:
            # 文件占用 / 权限不足 → 任务失败，不修改任何状态
            raise ValueError(f"文件移动失败（可能被占用或无权限）: {e}")
    # else: 文件不存在，跳过移动，进入 DB 清理

    # 2. 数据库事务（显式 commit 以便在失败时执行文件补偿）
    removed_items = 0
    affected_playlists: list[Playlist] = []
    try:
        # 收集受影响的 PlaylistItem 和 Playlist
        items = (
            db.query(PlaylistItem)
            .filter(PlaylistItem.track_id == track_id)
            .all()
        )
        affected_playlist_ids = {it.playlist_id for it in items}
        if affected_playlist_ids:
            affected_playlists = (
                db.query(Playlist)
                .filter(
                    Playlist.id.in_(affected_playlist_ids),
                    Playlist.deleted_at.is_(None),
                )
                .all()
            )

        # 软删除曲目
        track.deleted_at = datetime.utcnow()
        # 删除所有 PlaylistItem 引用
        for it in items:
            db.delete(it)
            removed_items += 1
        # 触发 Playlist.updated_at 自动更新
        now = datetime.utcnow()
        for pl in affected_playlists:
            pl.updated_at = now

        # 版本戳：tracks 和 playlists 都要打戳
        bump_and_stamp(db, ENTITY_TRACKS, [track])
        bump_and_stamp(db, ENTITY_PLAYLISTS, affected_playlists)

        # 审计日志
        write_audit_log(
            db,
            username=task.submitted_by,
            action="track_delete",
            target_type="track",
            target_id=track_id,
            detail={
                "rel_path": track.rel_path,
                "file_exists_before": file_exists,
                "removed_node_playlist_items": removed_items,
                "affected_playlist_ids": list(affected_playlist_ids),
            },
            task_id=task.id,
        )

        db.commit()
    except Exception as commit_err:
        # 数据库提交失败 → 补偿：把隔离文件恢复到原路径
        db.rollback()
        if trash_path is not None and trash_path.exists():
            try:
                os.rename(str(trash_path), str(track_abs))
                logger.error(
                    "track_delete 数据库提交失败，已把文件恢复到原路径: %s (track_id=%d, task_id=%d, err=%s)",
                    track_abs, track_id, task.id, commit_err,
                )
            except OSError as restore_err:
                # 严重：文件已隔离但数据库回滚后无法恢复，需运维介入
                logger.critical(
                    "track_delete 数据库提交失败且文件恢复失败！隔离文件: %s (track_id=%d, task_id=%d, commit_err=%s, restore_err=%s)",
                    trash_path, track_id, task.id, commit_err, restore_err,
                )
        else:
            logger.error(
                "track_delete 数据库提交失败（无文件需恢复）: track_id=%d task_id=%d err=%s",
                track_id, task.id, commit_err,
            )
        raise  # 让 TaskExecutor 标记任务为 failed

    # 3. 数据库提交成功 → 永久删除隔离文件（best-effort）
    warning: Optional[str] = None
    if trash_path is not None and trash_path.exists():
        try:
            trash_path.unlink()
        except OSError as e:
            # 数据库删除仍视为成功，但返回 warning
            warning = f"隔离文件清理失败，请运维处理: {trash_path}"
            logger.warning(
                "track_delete 隔离文件清理失败: %s (track_id=%d, task_id=%d, err=%s)",
                trash_path, track_id, task.id, e,
            )

    return {
        "track_id": track_id,
        "file_deleted": file_exists,
        "file_missing": not file_exists,
        "removed_node_playlist_items": removed_items,
        "relative_path": track.rel_path,
        "warning": warning,
    }


# ---- 注册入口 ----

def register_all_handlers(executor: TaskExecutor) -> None:
    """注册所有内置任务处理器"""
    executor.register_handler("scan", _handle_scan)
    executor.register_handler("upload", _handle_upload)
    executor.register_handler("import_m3u", handle_import_m3u)
    executor.register_handler("track_delete", _handle_track_delete)
    logger.info("已注册 %d 个任务处理器", 4)
