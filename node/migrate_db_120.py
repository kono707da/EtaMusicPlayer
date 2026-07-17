"""一次性迁移脚本：给 1.1.0 的 eta_node 数据库补充 1.2.0 新增列

新增内容：
- tracks 表: deleted_at (DATETIME, nullable, index), version_stamp (INTEGER NOT NULL DEFAULT 0, index)
- playlists 表: deleted_at (同上), version_stamp (同上)
- data_versions 表: 由 SQLAlchemy create_all 自动创建，本脚本不处理

用法: python migrate_db_120.py <db_path>
"""
import sqlite3
import sys


def migrate(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for table in ("tracks", "playlists"):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            print(f"=== {table} 现有列: {cols}")

            if "deleted_at" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at DATETIME")
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_deleted_at ON {table}(deleted_at)"
                )
                print(f"  [+] 已添加 {table}.deleted_at 列 + 索引")
            else:
                print(f"  [ok] {table}.deleted_at 已存在，跳过")

            if "version_stamp" not in cols:
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN version_stamp INTEGER NOT NULL DEFAULT 0"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_version_stamp ON {table}(version_stamp)"
                )
                print(f"  [+] 已添加 {table}.version_stamp 列 + 索引")
            else:
                print(f"  [ok] {table}.version_stamp 已存在，跳过")

        conn.commit()
        print("\n=== 迁移后验证 ===")
        for table in ("tracks", "playlists"):
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            print(f"{table} 列: {cols}")

        print("\n=== data_versions 表是否存在 ===")
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        print(f"所有表: {tables}")
        if "data_versions" not in tables:
            print("  [!] data_versions 表不存在，将由 eta_node 启动时 create_all 自动创建")

        print("\n迁移完成")
    finally:
        conn.close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else r"D:\node_release\data\etamusic.db"
    print(f"迁移数据库: {db}\n")
    migrate(db)
