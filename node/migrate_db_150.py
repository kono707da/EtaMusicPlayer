"""一次性迁移脚本：1.5.0 播放列表文件夹

新增内容：
- 新表 playlist_folders: id/name/parent_id/owner_id/created_at/updated_at/deleted_at/version_stamp
- playlists 表新增列 folder_id (INTEGER, nullable, FK->playlist_folders.id, ON DELETE SET NULL)

设计要点：
- 不删除/不修改既有列，只 ADD COLUMN + CREATE TABLE，旧库无副作用
- 启动时由 eta_node.plugin.bootstrap 自动调用 ensure_columns(engine)
- 也可手动执行: python migrate_db_150.py <db_path>
"""
from __future__ import annotations

import sqlite3
import sys


def _existing_tables(conn: sqlite3.Connection) -> list[str]:
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]


def _existing_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def migrate(conn: sqlite3.Connection) -> dict:
    """对给定 SQLite 连接执行 1.5.0 迁移，幂等

    Returns: {"added": [...], "skipped": [...]}
    """
    added: list[str] = []
    skipped: list[str] = []

    tables = _existing_tables(conn)

    # 1. 创建 playlist_folders 表
    if "playlist_folders" not in tables:
        conn.execute(
            """
            CREATE TABLE playlist_folders (
                id INTEGER PRIMARY KEY,
                name VARCHAR(256) NOT NULL,
                parent_id INTEGER REFERENCES playlist_folders(id) ON DELETE CASCADE,
                owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                deleted_at DATETIME,
                version_stamp INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute("CREATE INDEX ix_playlist_folders_parent_id ON playlist_folders(parent_id)")
        conn.execute("CREATE INDEX ix_playlist_folders_owner_id ON playlist_folders(owner_id)")
        conn.execute("CREATE INDEX ix_playlist_folders_deleted_at ON playlist_folders(deleted_at)")
        conn.execute("CREATE INDEX ix_playlist_folders_version_stamp ON playlist_folders(version_stamp)")
        added.append("playlist_folders table + indexes")
    else:
        skipped.append("playlist_folders table")

    # 2. playlists 表加 folder_id 列
    if "playlists" in tables:
        cols = _existing_columns(conn, "playlists")
        if "folder_id" not in cols:
            conn.execute("ALTER TABLE playlists ADD COLUMN folder_id INTEGER REFERENCES playlist_folders(id) ON DELETE SET NULL")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_playlists_folder_id ON playlists(folder_id)")
            added.append("playlists.folder_id + index")
        else:
            skipped.append("playlists.folder_id")

    conn.commit()
    return {"added": added, "skipped": skipped}


def ensure_columns_from_url(database_url: str) -> None:
    """从 SQLAlchemy database_url 解析路径并执行迁移"""
    if not database_url.startswith("sqlite:///"):
        return
    db_path = database_url.replace("sqlite:///", "", 1)
    conn = sqlite3.connect(db_path)
    try:
        result = migrate(conn)
        for a in result["added"]:
            print(f"[migrate_150] + {a}")
        for s in result["skipped"]:
            print(f"[migrate_150] ok {s} (already exists)")
    finally:
        conn.close()


def ensure_columns(engine) -> None:
    """通过 SQLAlchemy engine 执行迁移（启动时调用）"""
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return
    ensure_columns_from_url(url)


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else r"D:\node_release\data\etamusic.db"
    print(f"迁移数据库: {db}\n")
    conn = sqlite3.connect(db)
    try:
        result = migrate(conn)
        for a in result["added"]:
            print(f"  [+] 已添加 {a}")
        for s in result["skipped"]:
            print(f"  [ok] {s} 已存在，跳过")
        print("\n迁移完成")
    finally:
        conn.close()
