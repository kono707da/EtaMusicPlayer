"""asmr_one 插件自身的数据库

存放：
- 设置（subdir/proxy/target_node 等）
- 下载任务记录

使用独立 SQLite 文件 data/asmr_one.db，与 local_node / access 隔离。
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import BASE_DIR

_db_path = BASE_DIR / "data" / "asmr_one.db"
_db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{_db_path.as_posix()}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.plugins.asmr_one import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
