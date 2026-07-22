"""m3u 播放列表导入处理

解析本机 m3u/m3u8 文件，将引用的音频文件复制或剪切到指定监控目录，
扫描入库后按 m3u 原始顺序创建播放列表。

支持两种导入模式：
1. 单个 m3u 文件：导入为一个播放列表（名称可自定义）
2. 文件夹递归：递归查找所有 m3u，每个 m3u 创建一个独立播放列表（名为 m3u 文件名）
   1.5.0 起：文件夹模式下保留 m3u 相对于导入根目录的层级关系，
   自动创建 PlaylistFolder 树，播放列表放到对应文件夹下。
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from eta_node.models import NodeTask, Playlist, PlaylistFolder, PlaylistItem, Track, User, WatchDir
from eta_node.scanner import scan_directory
from eta_node.task_executor import write_audit_log
from eta_node.versioning import bump_version, ENTITY_PLAYLISTS

logger = logging.getLogger("eta_node.m3u_importer")

# m3u 文件扩展名
M3U_EXTS = {".m3u", ".m3u8"}


def _parse_m3u(m3u_path: str) -> list[str]:
    """解析 m3u 文件，返回音频文件绝对路径列表（保持原顺序）

    路径可能是相对路径（基于 m3u 所在目录）或绝对路径。
    尝试 UTF-8（含 BOM）和 GBK 编码以兼容不同来源的 m3u。
    """
    p = Path(m3u_path)
    if not p.exists() or not p.is_file():
        return []
    base = p.parent
    entries: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with open(p, "r", encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    ref = Path(line)
                    if not ref.is_absolute():
                        ref = (base / ref).resolve()
                    entries.append(str(ref))
            break
        except UnicodeDecodeError:
            continue
    return entries


def _collect_m3u_files(payload: dict) -> list[tuple[str, str, list[str]]]:
    """收集要导入的 m3u 文件，返回 [(m3u_path, playlist_name, folder_parts), ...]

    folder_parts 是 m3u 相对于导入根目录的父目录路径组件列表（不含 m3u 文件名）。
    例如导入根 /Music，m3u 在 /Music/Artist1/Album1/playlist.m3u，
    则 folder_parts = ["Artist1", "Album1"]。

    单文件模式 folder_parts = []。
    """
    result: list[tuple[str, str, list[str]]] = []
    folder = payload.get("folder_path")
    single = payload.get("m3u_path")
    custom_name = (payload.get("playlist_name") or "").strip()

    if folder:
        root = Path(folder).resolve()
        if root.exists() and root.is_dir():
            for m3u in sorted(root.rglob("*")):
                if m3u.is_file() and m3u.suffix.lower() in M3U_EXTS:
                    # 计算相对于 root 的父目录路径
                    rel_parent = m3u.parent.relative_to(root)
                    if str(rel_parent) == ".":
                        folder_parts: list[str] = []
                    else:
                        folder_parts = [p for p in rel_parent.parts if p]
                    result.append((str(m3u), m3u.stem, folder_parts))
    elif single:
        p = Path(single)
        if p.exists() and p.is_file() and p.suffix.lower() in M3U_EXTS:
            name = custom_name or p.stem
            result.append((str(p), name, []))
    return result


def _ensure_folder_path(
    db: Session, folder_parts: list[str], owner_id: int,
    root_parent_id: Optional[int] = None,
) -> Optional[int]:
    """按 folder_parts 逐级创建文件夹，返回最内层文件夹 id

    folder_parts 为空时返回 root_parent_id（可能是 None=根级 或 指定文件夹 id）。
    root_parent_id 非空时，导入的层级根挂在此文件夹下（用于"导入到指定文件夹"场景）。
    同级同名文件夹复用（不重复创建）。
    """
    if not folder_parts:
        return root_parent_id

    parent_id: Optional[int] = root_parent_id
    for name in folder_parts:
        existing = (
            db.query(PlaylistFolder)
            .filter(
                PlaylistFolder.name == name,
                PlaylistFolder.parent_id == parent_id if parent_id is not None else PlaylistFolder.parent_id.is_(None),
                PlaylistFolder.owner_id == owner_id,
                PlaylistFolder.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            parent_id = existing.id
        else:
            folder = PlaylistFolder(
                name=name,
                parent_id=parent_id,
                owner_id=owner_id,
            )
            db.add(folder)
            db.flush()
            parent_id = folder.id
    return parent_id


def _unique_target(watch_dir_path: str, filename: str) -> Path:
    """在 watch_dir 内生成不冲突的目标路径（同名文件自动加序号）"""
    target = Path(watch_dir_path) / filename
    if not target.exists():
        return target
    stem = Path(filename).stem
    ext = Path(filename).suffix
    i = 1
    while True:
        candidate = Path(watch_dir_path) / f"{stem}_{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1


def _resolve_owner_id(db: Session, username: Optional[str]) -> int:
    """根据提交者用户名解析 owner_id，找不到则用第一个 admin"""
    if username:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return user.id
    admin = db.query(User).filter(User.is_admin.is_(True)).first()
    return admin.id if admin else 1


def handle_import_m3u(
    db: Session, payload: Optional[dict], task: NodeTask
) -> Optional[dict]:
    """m3u 播放列表导入任务处理器

    payload:
        m3u_path: str | None       单个 m3u 文件路径
        folder_path: str | None    文件夹路径（递归查找 m3u）
        watch_dir_id: int          目标监控目录 ID
        mode: str                  "copy" | "move"
        playlist_name: str         播放列表名（仅单个 m3u 模式生效）
        target_folder_id: int | None  目标文件夹 ID（导入的播放列表/层级挂在此文件夹下）
    """
    if not payload:
        raise ValueError("缺少导入参数")

    watch_dir_id = payload.get("watch_dir_id")
    mode = payload.get("mode", "copy")
    if mode not in ("copy", "move"):
        raise ValueError(f"不支持的 mode: {mode}")

    wd = db.get(WatchDir, watch_dir_id)
    if wd is None:
        raise ValueError(f"监控目录不存在: {watch_dir_id}")

    m3u_files = _collect_m3u_files(payload)
    if not m3u_files:
        raise ValueError("未找到可导入的 m3u 文件")

    owner_id = _resolve_owner_id(db, task.submitted_by)

    # 校验目标文件夹（如果指定）
    target_folder_id = payload.get("target_folder_id")
    if target_folder_id is not None:
        target_folder = db.get(PlaylistFolder, target_folder_id)
        if target_folder is None or target_folder.deleted_at is not None:
            raise ValueError(f"目标文件夹不存在: {target_folder_id}")
        if target_folder.owner_id != owner_id:
            # admin 可操作所有用户文件夹，非 admin 仅能操作自己的
            user = db.query(User).filter(User.id == owner_id).first()
            if not user or not user.is_admin:
                raise ValueError("无权操作目标文件夹")

    # ---- 阶段 1：解析所有 m3u 并复制/移动音频文件 ----
    # m3u_path -> (playlist_name, folder_parts, [(filename_in_watch_dir, abs_path), ...])
    m3u_entries: dict[str, tuple[str, list[str], list[tuple[str, str]]]] = {}
    total_files = 0
    copied = 0
    failed: list[str] = []

    for m3u_path, pl_name, folder_parts in m3u_files:
        audio_paths = _parse_m3u(m3u_path)
        file_list: list[tuple[str, str]] = []
        for src_path in audio_paths:
            total_files += 1
            src = Path(src_path)
            if not src.exists():
                failed.append(src_path)
                continue
            target = _unique_target(wd.path, src.name)
            try:
                if mode == "move":
                    shutil.move(str(src), str(target))
                else:
                    shutil.copy2(str(src), str(target))
                copied += 1
                file_list.append((target.name, str(target)))
            except Exception as e:
                failed.append(f"{src_path}: {e}")
            # 更新进度（阶段 1 占 0-50%）
            if total_files % 20 == 0 or total_files == len(audio_paths):
                task.progress = min(50, int(copied / max(total_files, 1) * 50))
                db.flush()
        m3u_entries[m3u_path] = (pl_name, folder_parts, file_list)

    # ---- 阶段 2：扫描入库 ----
    task.progress = 55
    db.flush()
    try:
        scan_directory(wd, db)
    except Exception as e:
        logger.exception("扫描入库失败")
        raise RuntimeError(f"扫描入库失败: {e}")

    task.progress = 75
    db.flush()

    # ---- 阶段 3：按 m3u 顺序创建播放列表并添加曲目 ----
    # 文件夹模式下，按 m3u 相对路径创建 PlaylistFolder 层级
    # target_folder_id 非空时，导入的层级根挂在该文件夹下
    playlists_created = []
    for m3u_path, (pl_name, folder_parts, file_list) in m3u_entries.items():
        folder_id = _ensure_folder_path(db, folder_parts, owner_id, root_parent_id=target_folder_id)
        pl = Playlist(
            name=pl_name,
            owner_id=owner_id,
            is_system=False,
            description=f"从 {Path(m3u_path).name} 导入",
            folder_id=folder_id,
        )
        db.add(pl)
        db.flush()

        position = 0
        added = 0
        for filename_in_wd, abs_path in file_list:
            track = (
                db.query(Track)
                .filter(
                    Track.watch_dir_id == wd.id,
                    Track.abs_path == abs_path,
                )
                .first()
            )
            if track is None:
                # abs_path 未匹配到，回退用 filename 匹配
                track = (
                    db.query(Track)
                    .filter(
                        Track.watch_dir_id == wd.id,
                        Track.filename == filename_in_wd,
                    )
                    .first()
                )
            if track is None:
                continue
            # 去重：同一播放列表不重复添加
            exists = (
                db.query(PlaylistItem)
                .filter(
                    PlaylistItem.playlist_id == pl.id,
                    PlaylistItem.track_id == track.id,
                )
                .first()
            )
            if exists:
                continue
            item = PlaylistItem(
                playlist_id=pl.id,
                track_id=track.id,
                position=position,
            )
            db.add(item)
            position += 1
            added += 1
        playlists_created.append(
            {
                "id": pl.id,
                "name": pl.name,
                "track_count": added,
                "m3u": Path(m3u_path).name,
            }
        )

    # 审计日志
    write_audit_log(
        db,
        username=task.submitted_by,
        action="import_m3u",
        target_type="watch_dir",
        target_id=wd.id,
        detail={
            "mode": mode,
            "m3u_count": len(m3u_files),
            "total_files": total_files,
            "copied": copied,
            "failed": len(failed),
            "playlists": [{"id": p["id"], "name": p["name"]} for p in playlists_created],
        },
        task_id=task.id,
    )

    task.progress = 100
    bump_version(db, ENTITY_PLAYLISTS)
    return {
        "playlists": playlists_created,
        "total_files": total_files,
        "copied": copied,
        "failed_count": len(failed),
        "failed_files": failed[:100],
    }
