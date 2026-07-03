"""去重配置与检测逻辑（字段可配置）"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.plugins.local_node.models import DedupConfig, Track


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


def _build_field_key(track: Track, fields: list[str], duration_tolerance: float) -> tuple:
    """为单个 track 构造分组键。file_hash 暂以 file_size 近似（未实现完整哈希）。"""
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
            # 暂未实现完整文件哈希，使用 file_size 作为近似键
            parts.append(track.file_size)
        else:
            parts.append(None)
    return tuple(parts)


def detect_duplicates(db: Session, config: Optional[DedupConfig] = None) -> list[dict]:
    """检测重复组

    按配置字段分组：duration 用容差比较（按容差归桶），file_size 完全相等，
    其他字符串忽略大小写并去除首尾空白后比较。返回重复组列表，每组含多个 track_id。
    """
    if config is None:
        config = get_config(db)
    if not config.enabled:
        return []

    fields = parse_fields(config)
    tol = config.duration_tolerance

    tracks = db.query(Track).all()

    groups: dict = defaultdict(list)
    for t in tracks:
        key = _build_field_key(t, fields, tol)
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
