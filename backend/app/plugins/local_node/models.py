"""全部 SQLAlchemy ORM 模型定义"""
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.plugins.local_node.database import Base


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

    cover_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lyrics_embedded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    format_priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )

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
    """扫描任务"""

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


# 系统播放列表名称常量
SYSTEM_PLAYLIST_ALL = "全部音乐"
SYSTEM_PLAYLIST_INBOX = "收集箱"
