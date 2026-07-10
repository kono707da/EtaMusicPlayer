"""任务处理器注册

所有写操作的处理器在此注册到 TaskExecutor。
每个处理器签名: (db: Session, payload: dict | None, task: NodeTask) -> dict | None
处理器内部不需要 commit（由 TaskExecutor 统一 commit），但可以 flush。
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from eta_node.models import NodeTask, TrackStats, WatchDir
from eta_node.scanner import scan_directory
from eta_node.task_executor import TaskExecutor, write_audit_log

logger = logging.getLogger("eta_node.task_handlers")


# ---- scan 处理器 ----

def _handle_scan(
    db: Session, payload: Optional[dict], task: NodeTask
) -> Optional[dict]:
    """扫描监控目录，将音频文件元数据入库

    payload:
        watch_dir_id: int | None  (None = 扫描所有启用的目录)
    """
    watch_dir_id = payload.get("watch_dir_id") if payload else None

    query = db.query(WatchDir).filter(WatchDir.enabled.is_(True))
    if watch_dir_id is not None:
        query = query.filter(WatchDir.id == watch_dir_id)
    watch_dirs = query.all()

    if not watch_dirs:
        return {"total_files": 0, "new_tracks": 0, "updated_tracks": 0, "message": "no enabled watch_dirs"}

    total_all = 0
    new_all = 0
    updated_all = 0
    total_dirs = len(watch_dirs)

    for i, wd in enumerate(watch_dirs):
        t, n, u = scan_directory(wd, db)
        total_all += t
        new_all += n
        updated_all += u

        # 更新进度
        task.progress = int((i + 1) / total_dirs * 100)
        db.flush()

    # 为新入库的 Track 创建 TrackStats（通过 file_mtime 判断是否是新入库）
    # scan_directory 内部已经 commit，这里补充 TrackStats
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
        },
        task_id=task.id,
    )

    return {
        "total_files": total_all,
        "new_tracks": new_all,
        "updated_tracks": updated_all,
    }


def _ensure_track_stats_for_recent(db: Session, watch_dirs: list[WatchDir]) -> None:
    """为缺少 TrackStats 的 Track 补充记录"""
    wd_ids = [wd.id for wd in watch_dirs]
    if not wd_ids:
        return

    from eta_node.models import Track
    from sqlalchemy import outerjoin, select

    # 找出没有 TrackStats 的 Track
    tracks_without_stats = (
        db.query(Track)
        .filter(Track.watch_dir_id.in_(wd_ids))
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


# ---- 注册入口 ----

def register_all_handlers(executor: TaskExecutor) -> None:
    """注册所有内置任务处理器"""
    executor.register_handler("scan", _handle_scan)
    executor.register_handler("upload", _handle_upload)
    logger.info("已注册 %d 个任务处理器", 2)
