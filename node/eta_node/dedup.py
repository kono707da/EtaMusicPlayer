"""去重配置与检测逻辑（字段可配置）

1.2.1 起：
- file_hash 字段使用真 SHA-256（按 file_size + file_mtime 缓存到 Track.file_hash 列）
- 仅在启用 file_hash 去重或显式检测时计算，避免每次扫描都读大文件
- 自动扫描不会因哈希相同自动删除或合并文件；哈希只用于提示重复组
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from eta_node.models import DedupConfig, Track


logger = logging.getLogger("eta_node.dedup")


# 支持的去重字段
DEDUP_FIELDS_AVAILABLE = [
    "title",
    "album",
    "artist",
    "duration",
    "file_size",
    "file_hash",
]

# 默认配置
DEFAULT_FIELDS = ["title", "album", "artist", "duration", "file_size"]
DEFAULT_DURATION_TOLERANCE = 1.0

# 流式哈希读取块大小（64KB）
_HASH_CHUNK_SIZE = 64 * 1024


def get_config(db: Session) -> DedupConfig:
    """获取去重配置，不存在则创建默认（id=1）"""
    cfg = db.get(DedupConfig, 1)
    if cfg is None:
        cfg = DedupConfig(
            id=1,
            fields=json.dumps(DEFAULT_FIELDS),
            duration_tolerance=DEFAULT_DURATION_TOLERANCE,
            enabled=True,
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def parse_fields(cfg: DedupConfig) -> list[str]:
    """解析配置的 JSON 字段数组"""
    try:
        fields = json.loads(cfg.fields)
        if isinstance(fields, list):
            return [str(f) for f in fields if f in DEDUP_FIELDS_AVAILABLE]
    except (json.JSONDecodeError, TypeError):
        pass
    return list(DEFAULT_FIELDS)


def _norm_str(value: Optional[str]) -> str:
    """字符串归一化：忽略大小写 + 去除首尾空白"""
    if value is None:
        return ""
    return value.strip().lower()


def compute_file_hash(file_path: str) -> Optional[str]:
    """流式计算文件的 SHA-256，返回十六进制字符串。

    文件不存在或读取失败时返回 None。
    """
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(_HASH_CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.warning("计算 file_hash 失败 %s: %s", file_path, e)
        return None


def get_track_file_hash(db: Session, track: Track) -> Optional[str]:
    """获取曲目的 SHA-256 file_hash，按 file_size + file_mtime 缓存。

    缓存逻辑：
    - 若 track.file_hash 不为空 且 track.file_hash_mtime == track.file_mtime
      且 track.file_size 未变化（用 file_mtime 间接判断），直接返回缓存
    - 否则重新计算并写回 Track.file_hash / file_hash_mtime
    - 计算失败（文件不存在等）返回 None，不写回缓存

    注意：调用方负责 commit。本函数只 flush。
    """
    # 文件元数据失效判断：mtime 变化或 file_hash 为空
    if (
        track.file_hash
        and track.file_hash_mtime is not None
        and track.file_mtime is not None
        and abs(track.file_hash_mtime - track.file_mtime) < 1e-3
    ):
        return track.file_hash

    # 重新计算
    if not track.abs_path:
        return None
    new_hash = compute_file_hash(track.abs_path)
    if new_hash is None:
        return None
    track.file_hash = new_hash
    track.file_hash_mtime = track.file_mtime
    db.flush()
    return new_hash


def _build_field_key(
    track: Track,
    fields: list[str],
    duration_tolerance: float,
    db: Optional[Session] = None,
) -> tuple:
    """为单个 track 构造分组键。

    1.2.1 起：file_hash 字段使用真 SHA-256（按 file_size + file_mtime 缓存）。
    需要传入 db 才能写回缓存；db 为 None 时跳过缓存写回，仅读取已有 hash。

    若 file_hash 字段启用但 track 无法计算哈希（文件丢失等），
    用 None 作为键值，避免与 file_size 误分组。
    """
    parts: list = []
    for f in fields:
        if f in ("title", "album", "artist"):
            parts.append(_norm_str(getattr(track, f, None)))
        elif f == "duration":
            dur = track.duration
            if dur is None:
                parts.append(None)
            else:
                # 用容差向下取整归桶
                bucket = int(dur / max(duration_tolerance, 0.001))
                parts.append(bucket)
        elif f == "file_size":
            parts.append(track.file_size)
        elif f == "file_hash":
            # 真 SHA-256（按需计算 + 缓存）
            if db is not None:
                h = get_track_file_hash(db, track)
            elif track.file_hash:
                # 仅读缓存，不计算
                h = track.file_hash
            else:
                h = None
            parts.append(h)
        else:
            parts.append(None)
    return tuple(parts)


def detect_duplicates(db: Session, config: Optional[DedupConfig] = None) -> list[dict]:
    """检测重复组

    按配置字段分组：duration 用容差比较（按容差归桶），file_size 完全相等，
    其他字符串忽略大小写并去除首尾空白后比较。返回重复组列表，每组含多个 track_id。

    1.2.1：
    - 排除软删除曲目
    - file_hash 字段使用真 SHA-256（按需计算 + 缓存），调用方负责 commit
    """
    if config is None:
        config = get_config(db)
    if not config.enabled:
        return []

    fields = parse_fields(config)
    tol = config.duration_tolerance

    tracks = db.query(Track).filter(Track.deleted_at.is_(None)).all()

    groups: dict = defaultdict(list)
    for t in tracks:
        # 传入 db 以便 file_hash 计算时写回缓存
        key = _build_field_key(t, fields, tol, db=db)
        groups[key].append(t)

    results: list[dict] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        # 对于 duration 容差桶可能误并，再做二次校验
        if "duration" in fields and tol > 0:
            # 仅保留桶内两两 duration 差 <= tol 的成员（按首元素校验）
            base = members[0].duration
            filtered = [
                m for m in members
                if (m.duration is None and base is None)
                or (m.duration is not None and base is not None and abs(m.duration - base) <= tol)
            ]
            if len(filtered) < 2:
                continue
            members = filtered

        # 构造可读 group_key
        key_parts = []
        for i, f in enumerate(fields):
            val = key[i] if i < len(key) else None
            key_parts.append(f"{f}={val}")
        results.append(
            {
                "group_key": "|".join(key_parts),
                "track_ids": [m.id for m in members],
            }
        )
    return results
