"""一次性迁移脚本：给 1.2.0 的 eta_node 数据库补充 1.2.1 新增列

新增内容：
- tracks 表:
    file_hash       TEXT (nullable, index)  — SHA-256 文件内容哈希
    file_hash_mtime FLOAT (nullable)         — 哈希计算时的 file_mtime，用于缓存失效判定

设计要点：
- 不删除/不修改既有列，只 ADD COLUMN，旧库无副作用
- 启动时由 eta_node.plugin.bootstrap 自动调用 migrate_db_121.ensure_columns(engine)
- 也可手动执行: python migrate_db_121.py <db_path>
"""
from __future__ import annotations

import sqlite3
import sys
from typing import Optional


def _existing_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _existing_indexes(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA index_list({table})").fetchall()
    return [r[1] for r in rows]


def migrate(conn: sqlite3.Connection) -> dict:
    """对给定 SQLite 连接执行 1.2.1 迁移，幂等

    Returns: {"added": [...], "skipped": [...]}
    """
    added: list[str] = []
    skipped: list[str] = []

    cols = _existing_columns(conn, "tracks")
    if "file_hash" not in cols:
        conn.execute("ALTER TABLE tracks ADD COLUMN file_hash TEXT")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_tracks_file_hash ON tracks(file_hash)"
        )
        added.append("tracks.file_hash + index")
    else:
        skipped.append("tracks.file_hash")

    if "file_hash_mtime" not in cols:
        conn.execute("ALTER TABLE tracks ADD COLUMN file_hash_mtime FLOAT")
        added.append("tracks.file_hash_mtime")
    else:
        skipped.append("tracks.file_hash_mtime")

    conn.commit()
    return {"added": added, "skipped": skipped}


def ensure_columns_from_url(database_url: str) -> None:
    """从 SQLAlchemy database_url 解析路径并执行迁移"""
    # 形如 sqlite:///path/to/db.sqlite
    if not database_url.startswith("sqlite:///"):
        return
    db_path = database_url.replace("sqlite:///", "", 1)
    conn = sqlite3.connect(db_path)
    try:
        result = migrate(conn)
        for a in result["added"]:
            print(f"[migrate_121] + {a}")
        for s in result["skipped"]:
            print(f"[migrate_121] ok {s} (already exists)")
    finally:
        conn.close()


def ensure_columns(engine) -> None:
    """通过 SQLAlchemy engine 执行迁移（启动时调用）

    使用原生 sqlite3 连接以避免和 ORM session 冲突。
    """
    from sqlalchemy import create_engine

    # engine 可能是 sqlite:///... URL
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return
    ensure_columns_from_url(url)


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else r"D:\node_release\data\etamusic.db"
    print(f"迁移数据库: {db}\n")
    conn = sqlite3.connect(db)
    try:
        # 打印迁移前状态
        cols_before = _existing_columns(conn, "tracks")
        print(f"=== tracks 现有列: {cols_before}")
        result = migrate(conn)
        print()
        for a in result["added"]:
            print(f"  [+] 已添加 {a}")
        for s in result["skipped"]:
            print(f"  [ok] {s} 已存在，跳过")
        print("\n=== 迁移后验证 ===")
        cols_after = _existing_columns(conn, "tracks")
        print(f"tracks 列: {cols_after}")
        print("\n迁移完成")
    finally:
        conn.close()
