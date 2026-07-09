"""bili_audio 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from eta_bili.database import Base


class BiliSetting(Base):
    """键值对设置"""

    __tablename__ = "bili_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class BiliSubscription(Base):
    """B站音频订阅"""

    __tablename__ = "bili_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(Integer, index=True)
    uname: Mapped[str] = mapped_column(String(256))
    last_check: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BiliDownloadTask(Base):
    """下载任务"""

    __tablename__ = "bili_download_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auid: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    target_base_url: Mapped[str] = mapped_column(String(256))
    target_watch_dir_id: Mapped[int] = mapped_column(Integer)
    target_subdir: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)

    files_json: Mapped[list] = mapped_column(JSON, default=list)
    selected_paths: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    total_files: Mapped[int] = mapped_column(Integer, default=0)
    completed_files: Mapped[int] = mapped_column(Integer, default=0)
    skipped_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)

    current_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    current_file_size: Mapped[int] = mapped_column(Integer, default=0)
    current_file_done: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cover_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
