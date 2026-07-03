"""数据库引擎、会话与基类定义"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


# SQLite 连接：开启外键约束
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

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
    from app.plugins.local_node import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
