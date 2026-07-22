"""netease_music 数据模型"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from eta_netease.database import Base


class Setting(Base):
    """键值对设置"""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DownloadTask(Base):
    """下载任务

    支持单曲下载和歌单批量下载。
    一个任务可包含多首歌曲，每首歌对应一个 DownloadFileStatus。
    """

    __tablename__ = "download_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 来源信息
    source_type: Mapped[str] = mapped_column(String(32), default="song")
    # song=单曲, playlist=歌单
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    source_title: Mapped[str] = mapped_column(String(512), default="")

    # 目标节点
    target_base_url: Mapped[str] = mapped_column(String(256), default="local_node")
    target_watch_dir_id: Mapped[int] = mapped_column(Integer, default=1)
    target_subdir: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    # pending/running/completed/failed/partial/canceled

    # 歌曲列表 JSON: [{song_id, name, artist, album, url, size, type, level}, ...]
    songs_json: Mapped[list] = mapped_column(JSON, default=list)
    selected_song_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    # 进度统计
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    completed_files: Mapped[int] = mapped_column(Integer, default=0)
    skipped_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)

    # 当前文件
    current_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    current_file_size: Mapped[int] = mapped_column(Integer, default=0)
    current_file_done: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 音质偏好
    level: Mapped[str] = mapped_column(String(32), default="exhigh")
    # standard/exhigh/lossless/hires

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DownloadFileStatus(Base):
    """单文件下载状态"""

    __tablename__ = "download_file_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, index=True)
    song_id: Mapped[int] = mapped_column(Integer, default=0, index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending/downloading/decrypting/completed/skipped/failed
    size: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    saved_to: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # 是否为 ncm 格式并已解密
    was_ncm: Mapped[bool] = mapped_column(Boolean, default=False)
    # 解密后的实际格式
    decrypted_format: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
