"""插件注册表 ORM 模型"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from eta_web.plugins_manager.database import Base


def _now() -> datetime:
    return datetime.utcnow()


class Plugin(Base):
    """已发现的插件注册记录

    - name：插件目录名（唯一）
    - enabled：是否启用（启动时只加载 enabled=True 的插件）
    - 来自 manifest.py 的元数据（description/version/author）
    """

    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    author: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )


class RemoteNode(Base):
    """远程节点配置

    统一管理远程 eta_node 实例的连接信息。
    前端工作台浏览曲库和下载插件推送文件共用同一套节点配置。
    """

    __tablename__ = "remote_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str] = mapped_column(String(128), default="admin", nullable=False)
    password: Mapped[str] = mapped_column(String(256), default="", nullable=False)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )
