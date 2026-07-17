"""节点数据缓存表：离线时供前端读取，置灰展示

设计要点：
- 缓存 tracks/playlists 元数据（不含音频文件），按 node_id 索引
- 节点在线时：前端直调节点 API（实时数据），缓存仅用于离线兜底
- 节点离线时：前端读缓存，曲目置灰，可查看元数据但不可播放
- 节点删除时：级联清理该节点的所有缓存 + 客户端播放列表引用
- 同步策略：进入工作台时比对 /api/version 的 data_versions，差异部分拉取增量
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from eta_web.plugins_manager.database import Base


def _now() -> datetime:
    return datetime.utcnow()


class NodeTrackCache(Base):
    """节点曲库缓存：每个节点的每首曲目一行"""

    __tablename__ = "node_track_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("remote_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # 节点侧曲目字段（元数据快照）
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
    cover_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lyrics_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    format_priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 缓存管理字段
    cached_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("node_id", "track_id", name="uq_node_track_cache"),
    )


class NodePlaylistCache(Base):
    """节点播放列表缓存：每个节点的每个播放列表一行（含曲目成员 JSON）"""

    __tablename__ = "node_playlist_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("remote_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    playlist_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    # 曲目成员：JSON 数组 [{track_id, position}, ...]
    items_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    cached_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("node_id", "playlist_id", name="uq_node_playlist_cache"),
    )


class NodeSyncState(Base):
    """节点同步状态：记录每个节点每个实体的最后同步版本号

    进入工作台时比对 /api/version 的 data_versions 与此表 last_sync_version，
    差异则拉取 /api/{entity}/changes?since_version=last_sync_version
    """

    __tablename__ = "node_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("remote_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="tracks | playlists")
    last_sync_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("node_id", "entity_type", name="uq_node_sync_state"),
    )
