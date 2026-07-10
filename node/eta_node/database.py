"""数据库引擎、会话与基类定义"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from eta_node.config import settings


# SQLite 连接：开启外键约束
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _connection_record) -> None:
    """每个新连接建立时设置 SQLite PRAGMA：
    - WAL 模式：读写并发，写不阻塞读
    - busy_timeout：写冲突时等待 5s 而非立即报错
    - foreign_keys：开启外键约束
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""

    pass


def get_db():
    """FastAPI 依赖：提供数据库会话并在请求结束后关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表（仅当表不存在时创建）"""
    # 必须先导入模型，确保元数据已注册
    from eta_node import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
