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
