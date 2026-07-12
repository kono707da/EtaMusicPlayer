"""客户端播放列表 ORM 模型

ClientPlaylist: 客户端播放列表（不属于任何节点）
ClientPlaylistItem: 播放列表曲目项（缓存元数据，支持跨节点）
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eta_web.plugins_manager.database import Base


def _now() -> datetime:
    return datetime.utcnow()


class ClientPlaylist(Base):
    """客户端播放列表

    不属于任何节点，可跨节点添加曲目。
    is_system=True 的列表（如"全部音乐"）不可删除。
    """

    __tablename__ = "client_playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )

    items: Mapped[list["ClientPlaylistItem"]] = relationship(
        "ClientPlaylistItem",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="ClientPlaylistItem.position",
    )


class ClientPlaylistItem(Base):
    """客户端播放列表曲目项

    缓存曲目元数据，节点失效后仍可显示（前端根据 node_id 判断节点是否在线）。
    position 维护每个播放列表私有的曲目顺序。
    """

    __tablename__ = "client_playlist_items"
    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", "node_id", name="uq_playlist_track_node"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    playlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("client_playlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    node_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 缓存的曲目元数据（节点失效时仍可显示）
    title: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    artist: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    album: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    playlist: Mapped["ClientPlaylist"] = relationship("ClientPlaylist", back_populates="items")
