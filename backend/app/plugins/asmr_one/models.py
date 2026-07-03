"""asmr_one 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.plugins.asmr_one.database import Base


class Setting(Base):
    """键值对设置"""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DownloadTask(Base):
    """下载任务"""

    __tablename__ = "download_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(Integer, index=True)
    work_title: Mapped[str] = mapped_column(String(512))
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # 目标节点信息（base_url + token）
    target_base_url: Mapped[str] = mapped_column(String(256))
    target_watch_dir_id: Mapped[int] = mapped_column(Integer)
    target_subdir: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # 状态：pending / running / completed / failed / partial / canceled
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)

    # 文件清单（JSON 数组：[{url, path, title, size, duration}, ...]）
    files_json: Mapped[list] = mapped_column(JSON, default=list)
    # 选中的文件（路径列表，与 files_json 中的 path 对应）；空 = 全选
    selected_paths: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    total_files: Mapped[int] = mapped_column(Integer, default=0)
    completed_files: Mapped[int] = mapped_column(Integer, default=0)
    skipped_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)

    # 当前正在下载的文件路径
    current_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # 当前文件已下载字节数 / 总字节数（仅用于实时进度展示，不持久化每次写入）
    current_file_size: Mapped[int] = mapped_column(Integer, default=0)
    current_file_done: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DownloadFileStatus(Base):
    """单文件下载状态（细化跟踪）"""

    __tablename__ = "download_file_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    # pending / downloading / completed / failed / skipped
    status: Mapped[str] = mapped_column(String(32), default="pending")
    size: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    saved_to: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
