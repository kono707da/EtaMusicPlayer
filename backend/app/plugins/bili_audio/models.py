from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.plugins.bili_audio.database import Base


class BiliDownloadTask(Base):
    __tablename__ = "bili_download_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bvid: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(500))
    upper_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    upper_mid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_index: Mapped[int] = mapped_column(Integer, default=0)
    page_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_quality: Mapped[int] = mapped_column(Integer, default=30280)
    output_format: Mapped[str] = mapped_column(String(10), default="mp3")
    target_watch_dir_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_subdir: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    saved_to: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BiliSetting(Base):
    __tablename__ = "bili_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")


class BiliSubscription(Base):
    __tablename__ = "bili_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    sub_type: Mapped[str] = mapped_column(String(32), default="collection")
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    upper_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    upper_mid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    downloaded_count: Mapped[int] = mapped_column(Integer, default=0)
    auto_download: Mapped[bool] = mapped_column(Boolean, default=True)
    audio_quality: Mapped[int] = mapped_column(Integer, default=30280)
    output_format: Mapped[str] = mapped_column(String(10), default="mp3")
    target_watch_dir_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_subdir: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
