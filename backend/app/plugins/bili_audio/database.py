from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "bili_audio.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app.plugins.bili_audio.models import BiliDownloadTask, BiliSetting

    Base.metadata.create_all(bind=engine)
