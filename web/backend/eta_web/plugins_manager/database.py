"""访问端骨架自身的数据库

与插件的数据库完全隔离，只存储访问端元数据（如插件注册表）。
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from eta_web.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

_db_path = BACKEND_DIR / "data" / "access.db"
_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{_db_path.as_posix()}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """访问端骨架 ORM 基类"""

    pass


def get_db():
    """FastAPI 依赖：提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表（仅当表不存在时创建）"""
    from eta_web.plugins_manager import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
