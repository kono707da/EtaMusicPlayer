"""全部 SQLAlchemy ORM 模型定义"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eta_node.database import Base


def _now() -> datetime:
    return datetime.utcnow()


class User(Base):
    """用户"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    playlists: Mapped[list["Playlist"]] = relationship(
        back_populates="owner", foreign_keys="Playlist.owner_id"
    )
    granted_permissions: Mapped[list["PlaylistPermission"]] = relationship(
        back_populates="user", foreign_keys="PlaylistPermission.user_id"
    )
    granted_by_permissions: Mapped[list["PlaylistPermission"]] = relationship(
        back_populates="granted_by_user", foreign_keys="PlaylistPermission.granted_by"
    )


class WatchDir(Base):
    """监控目录"""

    __tablename__ = "watch_dirs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    recursive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    tracks: Mapped[list["Track"]] = relationship(back_populates="watch_dir")


class Track(Base):
    """曲目"""

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watch_dir_id: Mapped[int] = mapped_column(
        ForeignKey("watch_dirs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rel_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    abs_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    ext: Mapped[str] = mapped_column(String(16), nullable=False, default="")

    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    artist: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    album: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    album_artist: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    track_no: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_mtime: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # SHA-256 文件内容哈希（仅在启用哈希去重或显式检测时计算，按 file_size + file_mtime 缓存）
    # 1.2.1 起：替代旧 dedup.py 中用 file_size 假装 file_hash 的伪实现
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    file_hash_mtime: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    cover_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lyrics_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    format_priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )
    # 软删除标记：节点侧不实际 DELETE，设置 deleted_at 后增量同步接口通知访问端清理缓存
    # 便于访问端离线时仍能展示该曲目元数据（置灰），直到用户手动删除节点注册
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    # 版本戳：记录该行最后一次变更时的 data_versions.version 值
    # 增量查询 WHERE version_stamp > since_version，实现真正的增量同步
    version_stamp: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    watch_dir: Mapped["WatchDir"] = relationship(back_populates="tracks")

    __table_args__ = (
        UniqueConstraint("watch_dir_id", "rel_path", name="uq_track_watchdir_relpath"),
    )


class Playlist(Base):
    """播放列表"""

    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )
    # 软删除标记：与 Track.deleted_at 同理，供访问端增量同步
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    # 版本戳：与 Track.version_stamp 同理
    version_stamp: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    owner: Mapped["User"] = relationship(
        back_populates="playlists", foreign_keys=[owner_id]
    )
    items: Mapped[list["PlaylistItem"]] = relationship(
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItem.position",
    )
    permissions: Mapped[list["PlaylistPermission"]] = relationship(
        back_populates="playlist", cascade="all, delete-orphan"
    )


class PlaylistItem(Base):
    """播放列表项"""

    __tablename__ = "playlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    playlist: Mapped["Playlist"] = relationship(back_populates="items")
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", name="uq_playlistitem_track"),
    )


class PlaylistPermission(Base):
    """播放列表授权"""

    __tablename__ = "playlist_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    granted_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    playlist: Mapped["Playlist"] = relationship(back_populates="permissions")
    user: Mapped["User"] = relationship(
        back_populates="granted_permissions", foreign_keys=[user_id]
    )
    granted_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="granted_by_permissions", foreign_keys=[granted_by]
    )

    __table_args__ = (
        UniqueConstraint("playlist_id", "user_id", name="uq_playlistpermission_user"),
    )


class PlayHistory(Base):
    """播放历史（节点级）"""

    __tablename__ = "play_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    played_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    client_info: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class DedupConfig(Base):
    """去重配置（单行，固定 id=1）"""

    __tablename__ = "dedup_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    fields: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default='["title","album","artist","duration","file_size"]',
    )
    duration_tolerance: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ScanTask(Base):
    """扫描任务（保留向后兼容，新代码使用 NodeTask）"""

    __tablename__ = "scan_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False, index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_tracks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_tracks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)


class NodeTask(Base):
    """节点通用任务（单线程任务队列）

    所有写操作通过任务队列串行执行，避免并发数据库写入冲突。
    访问端只提交任务请求，节点自主调度执行。
    """

    __tablename__ = "node_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="scan|upload|playlist_add|playlist_remove|playlist_reorder|"
                "metadata_update|metadata_rename|watch_dir_create|watch_dir_update|"
                "watch_dir_delete|user_create|user_update|user_delete|"
                "permission_grant|permission_revoke|dedup_update",
    )
    status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False, index=True,
        comment="pending|running|completed|failed|cancelled",
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True,
        comment="10=用户交互, 0=默认, -10=后台任务",
    )
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    submitted_by: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="提交者用户名"
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, nullable=False, index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    """审计日志：记录何时哪个访问端用哪个用户做了什么重要操作"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=_now, nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)


class TrackStats(Base):
    """曲目统计：文件元数据之外的统计数据"""

    __tablename__ = "track_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    total_play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_skip_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_complete_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_played_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class UserPlayStats(Base):
    """用户播放统计：每个用户对每首曲目的播放记录"""

    __tablename__ = "user_play_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skip_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    complete_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_userplaystats_user_track"),
    )


class DataVersion(Base):
    """数据版本号表：记录曲库/播放列表的数据版本，供访问端增量同步比对

    entity_type 取值：
    - 'tracks':   曲库变更（扫描入库、元数据编辑、去重删除、音质替换）
    - 'playlists': 播放列表变更（CRUD、增删曲目、m3u 导入、重排序）

    每次数据变更在同一事务内 version += 1，访问端通过 /api/version 读取当前版本号，
    与本地 node_sync_state.last_sync_version 比对决定是否拉取增量。
    """
    __tablename__ = "data_versions"

    entity_type: Mapped[str] = mapped_column(
        String(32), primary_key=True, comment="tracks | playlists"
    )
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PlaybackSettings(Base):
    """播放完成判定配置（单行表，id=1）

    用于区分音乐和广播剧的播放完成百分比：
    - 曲目时长 >= duration_threshold_seconds 视为广播剧，应用 broadcast_complete_percent
    - 曲目时长 <  duration_threshold_seconds 视为音乐，应用 music_complete_percent
    - 前端播放器在进度达到对应百分比时上报 complete 事件（仅记统计，不自动切歌）

    默认值：分界 900 秒（15 分钟）/ 音乐 90% / 广播剧 70%
    """
    __tablename__ = "playback_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    duration_threshold_seconds: Mapped[int] = mapped_column(
        Integer, default=900, nullable=False,
        comment="音乐/广播剧分界时长（秒），默认 900=15 分钟",
    )
    music_complete_percent: Mapped[int] = mapped_column(
        Integer, default=90, nullable=False,
        comment="音乐完成百分比（0-100），默认 90",
    )
    broadcast_complete_percent: Mapped[int] = mapped_column(
        Integer, default=70, nullable=False,
        comment="广播剧完成百分比（0-100），默认 70",
    )


# 系统播放列表名称常量
SYSTEM_PLAYLIST_ALL = "全部音乐"
SYSTEM_PLAYLIST_INBOX = "收集箱"
