"""数据版本号管理：为访问端增量同步提供变更追踪

设计要点：
- 版本号持久化在 data_versions 表，节点重启不重置
- bump_version 必须在与业务写入同一个事务内调用（调用方负责 commit）
- Track/Playlist 有 version_stamp 列，bump_and_stamp 会将新版本号写到受影响记录
- 增量接口 /api/{entity}/changes?since_version=N 返回 version_stamp > N 的记录
- 访问端比对 /api/version 中的 data_versions 与本地 last_sync_version 决定是否拉取

entity_type 取值：
- 'tracks':   曲库变更（扫描、元数据编辑、去重删除、音质替换）
- 'playlists': 播放列表变更（CRUD、增删曲目、m3u 导入、重排序）
"""
from __future__ import annotations

from typing import Iterable

from sqlalchemy.orm import Session

from eta_node.models import DataVersion, Track, Playlist

# entity_type 常量，避免拼写错误
ENTITY_TRACKS = "tracks"
ENTITY_PLAYLISTS = "playlists"


def get_version(db: Session, entity_type: str) -> int:
    """读取指定实体的当前版本号，不存在则返回 0"""
    row = db.get(DataVersion, entity_type)
    return row.version if row else 0


def get_all_versions(db: Session) -> dict[str, int]:
    """读取所有实体的版本号，供 /api/version 返回"""
    rows = db.query(DataVersion).all()
    return {r.entity_type: r.version for r in rows} if rows else {}


def bump_version(db: Session, entity_type: str) -> int:
    """递增版本号并自动给当前 session 中 dirty/new 的对应模型打戳

    自动从 session.new 和 session.dirty 中筛选 Track 或 Playlist 对象，
    将新版本号写入其 version_stamp 列。调用方无需手动收集受影响记录。

    对于批量 UPDATE 语句（如 .update() 不加载对象到 session），
    受影响记录不在 session.dirty 中，需改用 bump_and_stamp 手动传入记录，
    或在 bump 后执行一条 UPDATE WHERE version_stamp < new_version。

    返回递增后的新版本号。
    """
    row = db.get(DataVersion, entity_type)
    if row is None:
        row = DataVersion(entity_type=entity_type, version=1)
        db.add(row)
    else:
        row.version += 1
    db.flush()
    new_version = row.version

    # 自动给 session 中 dirty/new 的对应模型打戳
    model_cls = Track if entity_type == ENTITY_TRACKS else Playlist
    for obj in list(db.new) + list(db.dirty):
        if isinstance(obj, model_cls):
            obj.version_stamp = new_version
    db.flush()
    return new_version


def bump_and_stamp(db: Session, entity_type: str, records: Iterable) -> int:
    """递增版本号并将新版本号写到受影响记录的 version_stamp 列

    适用场景：已知受影响的 Track/Playlist 对象列表时，一次性完成版本号递增 + 打戳。
    对于批量操作（扫描入库新增100首），传入这100个 Track 对象即可。
    对于软删除，传入被软删除的对象。
    对于"全表可能受影响"的批量更新，可用 bump_version + 批量 UPDATE 语句。

    Args:
        db: 数据库会话
        entity_type: 'tracks' 或 'playlists'
        records: 受影响的 Track 或 Playlist 对象列表（已 db.add 或已修改的）

    Returns: 递增后的新版本号
    """
    new_version = bump_version(db, entity_type)
    for r in records:
        r.version_stamp = new_version
    db.flush()
    return new_version


def ensure_versions_initialized(db: Session) -> None:
    """初始化两条版本号记录（若不存在），用于数据库迁移后首次启动"""
    for entity in (ENTITY_TRACKS, ENTITY_PLAYLISTS):
        if db.get(DataVersion, entity) is None:
            db.add(DataVersion(entity_type=entity, version=0))
    db.commit()

