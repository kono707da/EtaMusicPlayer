"""1.2.1 客户端播放列表清理 - 访问端单元测试（无 pytest 框架）

验证：
1. DELETE /api/client-playlists/items/by-track 跨列表删除匹配项，幂等
2. _apply_track_changes 收到 deleted=true 时清理 ClientPlaylistItem

运行：python -m web.backend.tests.test_client_playlist_cleanup
或：python web/backend/tests/test_client_playlist_cleanup.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 让脚本能直接 import eta_web.*
# __file__ = web/backend/tests/test_xxx.py → 需把 web/backend 加进 sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from eta_web.plugins_manager.database import Base
from eta_web.plugins_manager.models import RemoteNode
from eta_web.client_playlists.models import ClientPlaylist, ClientPlaylistItem
from eta_web.node_cache.models import NodeTrackCache


_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  [PASS] {name}")
    else:
        _fail += 1
        print(f"  [FAIL] {name} {detail}")


def _make_test_db():
    """内存 SQLite，建表"""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=eng)
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    return Session(), eng


def _seed_remote_node(db, node_id: int = 1, name: str = "node1") -> RemoteNode:
    n = RemoteNode(
        id=node_id,
        name=name,
        url=f"http://node{node_id}.test",
        username="admin",
        password="x",
        enabled=True,
        is_active=True,
    )
    db.add(n)
    db.commit()
    return n


def _seed_client_playlists(db):
    """创建 2 个客户端播放列表，每个加 2 条引用 node=remote-1 的曲目"""
    pl1 = ClientPlaylist(name="pl1", is_system=False)
    pl2 = ClientPlaylist(name="pl2", is_system=False)
    pl_all = ClientPlaylist(name="全部音乐", is_system=True)
    db.add_all([pl1, pl2, pl_all])
    db.commit()
    db.refresh(pl1)
    db.refresh(pl2)
    db.refresh(pl_all)

    # pl1: track 1 + track 2 (都来自 remote-1)
    db.add_all([
        ClientPlaylistItem(playlist_id=pl1.id, track_id=1, node_id="remote-1",
                           position=0, title="t1", artist="a1"),
        ClientPlaylistItem(playlist_id=pl1.id, track_id=2, node_id="remote-1",
                           position=1, title="t2", artist="a2"),
    ])
    # pl2: track 1 (remote-1) + track 3 (remote-2)
    db.add_all([
        ClientPlaylistItem(playlist_id=pl2.id, track_id=1, node_id="remote-1",
                           position=0, title="t1", artist="a1"),
        ClientPlaylistItem(playlist_id=pl2.id, track_id=3, node_id="remote-2",
                           position=1, title="t3", artist="a3"),
    ])
    # pl_all: track 1 (remote-1)
    db.add_all([
        ClientPlaylistItem(playlist_id=pl_all.id, track_id=1, node_id="remote-1",
                           position=0, title="t1", artist="a1"),
    ])
    db.commit()
    return pl1, pl2, pl_all


def test_remove_items_by_track_basic() -> None:
    """按 (node_id, track_id) 跨列表删除：命中多个列表"""
    print("\n=== test_remove_items_by_track_basic ===")
    db, _eng = _make_test_db()
    _seed_remote_node(db, node_id=1, name="node1")
    pl1, pl2, pl_all = _seed_client_playlists(db)

    # 删除 (remote-1, track_id=1)：应删除 pl1 + pl2 + pl_all 各 1 条 = 3 条
    from eta_web.client_playlists.routers import remove_items_by_track, RemoveByTrackRequest
    req = RemoveByTrackRequest(node_id="remote-1", track_id=1)
    result = remove_items_by_track(req, db)

    check("ok=true", result.get("ok") is True)
    check("removed=3", result.get("removed") == 3, f"got {result.get('removed')}")

    # 验证 pl1 中 track 1 已删除，track 2 保留
    items_pl1 = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.playlist_id == pl1.id
    ).order_by(ClientPlaylistItem.position).all()
    check("pl1 剩 1 条", len(items_pl1) == 1, f"left {len(items_pl1)}")
    check("pl1 剩的是 track 2", items_pl1[0].track_id == 2)
    # position 重排为 0
    check("pl1 position 已重排", items_pl1[0].position == 0)

    # pl2 中 track 1 已删除，track 3 保留
    items_pl2 = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.playlist_id == pl2.id
    ).all()
    check("pl2 剩 1 条", len(items_pl2) == 1)
    check("pl2 剩的是 track 3", items_pl2[0].track_id == 3)

    # pl_all 中 track 1 已删除
    items_all = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.playlist_id == pl_all.id
    ).all()
    check("pl_all 已清空", len(items_all) == 0)


def test_remove_items_by_track_idempotent() -> None:
    """幂等：再次调用同一 (node_id, track_id) 返回 removed=0"""
    print("\n=== test_remove_items_by_track_idempotent ===")
    db, _eng = _make_test_db()
    _seed_remote_node(db, node_id=1)
    _seed_client_playlists(db)

    from eta_web.client_playlists.routers import remove_items_by_track, RemoveByTrackRequest

    # 第一次：删除 (remote-1, track 1)
    req = RemoveByTrackRequest(node_id="remote-1", track_id=1)
    r1 = remove_items_by_track(req, db)
    check("第一次 removed=3", r1["removed"] == 3)

    # 第二次：再调用一次
    r2 = remove_items_by_track(req, db)
    check("第二次 removed=0（幂等）", r2["removed"] == 0)


def test_remove_items_by_track_no_match() -> None:
    """不存在的 (node_id, track_id) 返回 removed=0"""
    print("\n=== test_remove_items_by_track_no_match ===")
    db, _eng = _make_test_db()
    _seed_remote_node(db, node_id=1)
    _seed_client_playlists(db)

    from eta_web.client_playlists.routers import remove_items_by_track, RemoveByTrackRequest
    req = RemoveByTrackRequest(node_id="remote-999", track_id=999)
    r = remove_items_by_track(req, db)
    check("removed=0", r["removed"] == 0)
    check("ok=true", r["ok"] is True)


def test_apply_track_changes_cleanup_client_refs() -> None:
    """_apply_track_changes 收到 deleted=true 时清理 ClientPlaylistItem + 标记 is_deleted"""
    print("\n=== test_apply_track_changes_cleanup_client_refs ===")
    db, _eng = _make_test_db()
    _seed_remote_node(db, node_id=1, name="node1")
    pl1, pl2, pl_all = _seed_client_playlists(db)

    # 预置 NodeTrackCache（track 1 + track 2，node_id=1）
    db.add_all([
        NodeTrackCache(node_id=1, track_id=1, title="t1", is_deleted=False),
        NodeTrackCache(node_id=1, track_id=2, title="t2", is_deleted=False),
    ])
    db.commit()

    # 调用 _apply_track_changes：track 1 被软删除
    from eta_web.node_cache.sync_service import _apply_track_changes
    changes = [
        {"id": 1, "deleted": True},
        {"id": 2, "deleted": False, "title": "t2-updated"},
    ]
    _apply_track_changes(db, node_id=1, changes=changes)
    db.commit()

    # track 1 缓存 is_deleted=true
    c1 = db.query(NodeTrackCache).filter(
        NodeTrackCache.node_id == 1, NodeTrackCache.track_id == 1
    ).one()
    check("track 1 is_deleted=true", c1.is_deleted is True)

    # track 2 缓存 is_deleted=false，title 已更新
    c2 = db.query(NodeTrackCache).filter(
        NodeTrackCache.node_id == 1, NodeTrackCache.track_id == 2
    ).one()
    check("track 2 is_deleted=false", c2.is_deleted is False)
    check("track 2 title 已更新", c2.title == "t2-updated")

    # ClientPlaylistItem 中所有 (remote-1, track 1) 都应被删除
    items_t1 = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.node_id == "remote-1",
        ClientPlaylistItem.track_id == 1,
    ).all()
    check("客户端引用已清理", len(items_t1) == 0, f"left {len(items_t1)}")

    # (remote-1, track 2) 应保留（未删除）
    items_t2 = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.node_id == "remote-1",
        ClientPlaylistItem.track_id == 2,
    ).all()
    check("未删除曲目引用保留", len(items_t2) == 1)

    # (remote-2, track 3) 应保留（其他节点）
    items_t3 = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.node_id == "remote-2",
        ClientPlaylistItem.track_id == 3,
    ).all()
    check("其他节点引用保留", len(items_t3) == 1)


def test_apply_track_changes_no_delete_when_not_deleted() -> None:
    """_apply_track_changes 普通 update 不清理客户端引用"""
    print("\n=== test_apply_track_changes_no_delete_when_not_deleted ===")
    db, _eng = _make_test_db()
    _seed_remote_node(db, node_id=1)
    _seed_client_playlists(db)

    db.add(NodeTrackCache(node_id=1, track_id=1, title="t1", is_deleted=False))
    db.commit()

    from eta_web.node_cache.sync_service import _apply_track_changes
    changes = [
        {"id": 1, "deleted": False, "title": "t1-renamed"},
    ]
    _apply_track_changes(db, node_id=1, changes=changes)
    db.commit()

    # ClientPlaylistItem 中 (remote-1, track 1) 应保留
    items = db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.node_id == "remote-1",
        ClientPlaylistItem.track_id == 1,
    ).all()
    check("普通 update 不清理引用", len(items) == 3, f"left {len(items)}")

    c = db.query(NodeTrackCache).filter(
        NodeTrackCache.node_id == 1, NodeTrackCache.track_id == 1
    ).one()
    check("title 已更新", c.title == "t1-renamed")
    check("is_deleted=false", c.is_deleted is False)


def main() -> int:
    print("=" * 60)
    print("1.2.1 客户端播放列表清理 - 访问端测试")
    print("=" * 60)

    test_remove_items_by_track_basic()
    test_remove_items_by_track_idempotent()
    test_remove_items_by_track_no_match()
    test_apply_track_changes_cleanup_client_refs()
    test_apply_track_changes_no_delete_when_not_deleted()

    print()
    print("=" * 60)
    print(f"结果: {_pass} 通过 / {_fail} 失败")
    print("=" * 60)
    return 0 if _fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
