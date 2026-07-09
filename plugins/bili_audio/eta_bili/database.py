"""bili_audio 插件自身的数据库

存放：
- 设置（cookie / target_node 等）
- 下载任务记录
- 订阅记录

使用独立 SQLite 文件 data/bili_audio.db，与 local_node / access 隔离。
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "bili_audio.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
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
    from eta_bili.models import BiliDownloadTask, BiliSetting, BiliSubscription  # noqa: F401

    Base.metadata.create_all(bind=engine)
