"""访问端自身的数据库

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
    """访问端 ORM 基类"""

    pass


def get_db():
    """FastAPI 依赖：提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表（仅当表不存在时创建）+ 轻量迁移（补齐新增列）"""
    from eta_web.plugins_manager import models  # noqa: F401
    from eta_web.client_playlists import models as _client_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _auto_migrate()

    # 初始化客户端系统播放列表
    from eta_web.client_playlists.routers import ensure_system_playlists
    with SessionLocal() as db:
        ensure_system_playlists(db)


def _auto_migrate() -> None:
    """轻量迁移：检查并补齐模型中新增的列

    SQLAlchemy create_all 不会给已有表添加新列，
    这里用 PRAGMA table_info 检测并 ALTER TABLE 补齐。
    """
    import sqlite3

    conn = sqlite3.connect(str(_db_path))
    try:
        # remote_nodes.is_active（v2 新增）
        cols = {row[1] for row in conn.execute("PRAGMA table_info(remote_nodes)")}
        if "is_active" not in cols:
            conn.execute(
                "ALTER TABLE remote_nodes ADD COLUMN is_active BOOLEAN DEFAULT 0 NOT NULL"
            )
            conn.commit()
    except sqlite3.OperationalError:
        pass  # 表不存在，create_all 会处理
    finally:
        conn.close()
