"""1.2.1 曲目删除与库一致性 - 节点侧单元测试（无 pytest 框架）

直接验证关键函数行为，使用临时 SQLite + 临时目录。
运行：python -m node.tests.test_track_delete
或：python node/tests/test_track_delete.py
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# 让脚本能直接 import eta_node.*
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from eta_node.database import Base
from eta_node.models import (
    AuditLog,
    DataVersion,
    NodeTask,
    Playlist,
    PlaylistItem,
    Track,
    User,
    WatchDir,
)
from eta_node.versioning import (
    ENTITY_PLAYLISTS,
    ENTITY_TRACKS,
    ensure_versions_initialized,
)
from eta_node.task_handlers import (
    TRASH_DIR_NAME,
    _handle_track_delete,
    _resolve_inside_watch_dir,
)
from eta_node.dedup import compute_file_hash
from eta_node.scanner import _cleanup_missing_tracks


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
    """创建内存 SQLite，建表，初始化版本号"""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=eng)
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    db = Session()
    ensure_versions_initialized(db)
    return db, eng


def _make_user(db) -> User:
    u = User(username="test_admin", password_hash="x", is_admin=True, is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _make_watch_dir(tmp_root: Path) -> Path:
    """在 tmp_root 下创建 watch_dir 目录，返回绝对路径"""
    wd_path = tmp_root / "music"
    wd_path.mkdir(parents=True, exist_ok=True)
    return wd_path


def test_resolve_inside_watch_dir() -> None:
    """路径安全校验：拒绝越界、目录、根本身"""
    print("\n=== test_resolve_inside_watch_dir ===")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # 普通文件应通过
        good = root / "a.mp3"
        good.write_text("x")
        try:
            ret = _resolve_inside_watch_dir(root, good)
            check("普通文件应通过", ret == good.resolve(), f"got {ret}")
        except ValueError as e:
            check("普通文件应通过", False, f"raised {e}")

        # 不存在的文件应抛错
        bad = root / "missing.mp3"
        try:
            _resolve_inside_watch_dir(root, bad)
            check("不存在文件应抛错", False)
        except (ValueError, FileNotFoundError, OSError):
            check("不存在文件应抛错", True)

        # 越界文件应抛错
        outside = Path(tmp) / ".." / "outside.mp3"
        # 创建上级目录中的文件
        (Path(tmp).parent / "outside.mp3").write_text("y") if not outside.exists() else None
        # 先在 root 外创建一个真实文件
        out_real = Path(tmp).parent / f"out_{os.getpid()}.mp3"
        out_real.write_text("z")
        try:
            _resolve_inside_watch_dir(root, out_real)
            check("越界文件应抛错", False)
        except (ValueError, FileNotFoundError, OSError):
            check("越界文件应抛错", True)
        finally:
            try:
                out_real.unlink()
            except OSError:
                pass

        # 目录应抛错（不是普通文件）
        sub_dir = root / "subdir"
        sub_dir.mkdir()
        try:
            _resolve_inside_watch_dir(root, sub_dir)
            check("目录应抛错", False)
        except ValueError:
            check("目录应抛错", True)


def test_compute_file_hash() -> None:
    """SHA-256 计算"""
    print("\n=== test_compute_file_hash ===")
    with tempfile.NamedTemporaryFile(delete=False) as f:
        content = b"hello world"
        f.write(content)
        path = f.name
    try:
        h = compute_file_hash(path)
        expected = hashlib.sha256(content).hexdigest()
        check("SHA-256 正确", h == expected, f"got {h}, want {expected}")
        check("SHA-256 长度 64", len(h or "") == 64)
    finally:
        os.unlink(path)


def test_handle_track_delete_basic() -> None:
    """_handle_track_delete 基本流程：文件存在 → 软删除 + 文件删除"""
    print("\n=== test_handle_track_delete_basic ===")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        wd_path = _make_watch_dir(tmp_root)

        db, _eng = _make_test_db()
        user = _make_user(db)
        wd = WatchDir(path=str(wd_path), recursive=True, enabled=True)
        db.add(wd)
        db.commit()
        db.refresh(wd)

        # 创建音频文件
        audio_path = wd_path / "song.mp3"
        audio_path.write_bytes(b"fake mp3 content")

        track = Track(
            watch_dir_id=wd.id,
            rel_path="song.mp3",
            abs_path=str(audio_path),
            filename="song.mp3",
            ext="mp3",
            title="song",
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        # 创建 Playlist + PlaylistItem
        pl = Playlist(name="pl1", owner_id=user.id, is_system=False)
        db.add(pl)
        db.commit()
        db.refresh(pl)
        item = PlaylistItem(playlist_id=pl.id, track_id=track.id, position=0)
        db.add(item)
        db.commit()

        # 构造 NodeTask
        task = NodeTask(
            task_type="track_delete",
            status="running",
            priority=10,
            payload={"track_id": track.id},
            submitted_by=user.username,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        result = _handle_track_delete(db, {"track_id": track.id}, task)

        check("返回 track_id", result["track_id"] == track.id)
        check("file_deleted=true", result["file_deleted"] is True)
        check("file_missing=false", result["file_missing"] is False)
        check("removed_node_playlist_items=1", result["removed_node_playlist_items"] == 1)
        check("warning=None", result.get("warning") is None)

        # 文件应已删除
        check("文件已删除", not audio_path.exists())

        # Track 应被软删除
        db.expire_all()
        t = db.get(Track, track.id)
        check("Track.deleted_at 已设置", t.deleted_at is not None)

        # PlaylistItem 应已删除
        items = db.query(PlaylistItem).filter(PlaylistItem.track_id == track.id).all()
        check("PlaylistItem 已删除", len(items) == 0)

        # trash 目录应为空（清理后）
        trash_dir = wd_path / TRASH_DIR_NAME
        if trash_dir.exists():
            leftover = list(trash_dir.iterdir())
            check("trash 目录为空", len(leftover) == 0, f"leftover: {leftover}")
        else:
            check("trash 目录为空", True)

        # 版本号应已递增
        from eta_node.versioning import get_version
        v_t = get_version(db, ENTITY_TRACKS)
        v_p = get_version(db, ENTITY_PLAYLISTS)
        check("tracks 版本号 > 0", v_t > 0)
        check("playlists 版本号 > 0", v_p > 0)

        # Track.version_stamp 应等于新版本号
        check("Track.version_stamp 已打戳", t.version_stamp == v_t)

        # 审计日志应已写入
        logs = db.query(AuditLog).filter(AuditLog.action == "track_delete").all()
        check("审计日志已写入", len(logs) == 1)


def test_handle_track_delete_file_missing() -> None:
    """_handle_track_delete 文件本已不存在"""
    print("\n=== test_handle_track_delete_file_missing ===")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        wd_path = _make_watch_dir(tmp_root)

        db, _eng = _make_test_db()
        user = _make_user(db)
        wd = WatchDir(path=str(wd_path), recursive=True, enabled=True)
        db.add(wd)
        db.commit()
        db.refresh(wd)

        # 不创建音频文件
        audio_path = wd_path / "ghost.mp3"

        track = Track(
            watch_dir_id=wd.id,
            rel_path="ghost.mp3",
            abs_path=str(audio_path),
            filename="ghost.mp3",
            ext="mp3",
            title="ghost",
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        task = NodeTask(
            task_type="track_delete",
            status="running",
            priority=10,
            payload={"track_id": track.id},
            submitted_by=user.username,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        result = _handle_track_delete(db, {"track_id": track.id}, task)

        check("file_deleted=false", result["file_deleted"] is False)
        check("file_missing=true", result["file_missing"] is True)
        check("removed_node_playlist_items=0", result["removed_node_playlist_items"] == 0)

        db.expire_all()
        t = db.get(Track, track.id)
        check("Track 仍被软删除", t.deleted_at is not None)


def test_handle_track_delete_idempotent() -> None:
    """_handle_track_delete 幂等：已软删除时再次调用返回成功"""
    print("\n=== test_handle_track_delete_idempotent ===")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        wd_path = _make_watch_dir(tmp_root)

        db, _eng = _make_test_db()
        user = _make_user(db)
        wd = WatchDir(path=str(wd_path), recursive=True, enabled=True)
        db.add(wd)
        db.commit()
        db.refresh(wd)

        audio_path = wd_path / "idem.mp3"
        audio_path.write_bytes(b"x")

        track = Track(
            watch_dir_id=wd.id,
            rel_path="idem.mp3",
            abs_path=str(audio_path),
            filename="idem.mp3",
            ext="mp3",
            title="idem",
            deleted_at=datetime.utcnow(),  # 已软删除
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        task = NodeTask(
            task_type="track_delete",
            status="running",
            payload={"track_id": track.id},
            submitted_by=user.username,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        result = _handle_track_delete(db, {"track_id": track.id}, task)

        check("幂等返回成功", result is not None)
        check("file_deleted=false", result["file_deleted"] is False)
        check("warning 包含已软删除", "已软删除" in (result.get("warning") or ""))

        # 文件应未被删除（因为直接跳过）
        check("文件未被删除", audio_path.exists())


def test_handle_track_delete_nonexistent_track() -> None:
    """_handle_track_delete 曲目不存在时返回 file_missing"""
    print("\n=== test_handle_track_delete_nonexistent_track ===")
    db, _eng = _make_test_db()
    user = _make_user(db)

    task = NodeTask(
        task_type="track_delete",
        status="running",
        payload={"track_id": 99999},
        submitted_by=user.username,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    result = _handle_track_delete(db, {"track_id": 99999}, task)

    check("幂等返回成功", result is not None)
    check("file_missing=true", result["file_missing"] is True)
    check("warning 包含不存在", "不存在" in (result.get("warning") or ""))


def test_cleanup_missing_tracks() -> None:
    """_cleanup_missing_tracks：未发现的曲目被软删除 + PlaylistItem 清理"""
    print("\n=== test_cleanup_missing_tracks ===")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        wd_path = _make_watch_dir(tmp_root)

        db, _eng = _make_test_db()
        user = _make_user(db)
        wd = WatchDir(path=str(wd_path), recursive=True, enabled=True)
        db.add(wd)
        db.commit()
        db.refresh(wd)

        # 三首曲目：found / missing / missing
        t_found = Track(
            watch_dir_id=wd.id, rel_path="found.mp3", abs_path=str(wd_path / "found.mp3"),
            filename="found.mp3", ext="mp3", title="found",
        )
        t_miss1 = Track(
            watch_dir_id=wd.id, rel_path="miss1.mp3", abs_path=str(wd_path / "miss1.mp3"),
            filename="miss1.mp3", ext="mp3", title="miss1",
        )
        t_miss2 = Track(
            watch_dir_id=wd.id, rel_path="miss2.mp3", abs_path=str(wd_path / "miss2.mp3"),
            filename="miss2.mp3", ext="mp3", title="miss2",
        )
        db.add_all([t_found, t_miss1, t_miss2])
        db.commit()
        db.refresh(t_found)
        db.refresh(t_miss1)
        db.refresh(t_miss2)

        # 给 missing 曲目各加一个 PlaylistItem
        pl = Playlist(name="pl", owner_id=user.id, is_system=False)
        db.add(pl)
        db.commit()
        db.refresh(pl)
        db.add_all([
            PlaylistItem(playlist_id=pl.id, track_id=t_miss1.id, position=0),
            PlaylistItem(playlist_id=pl.id, track_id=t_miss2.id, position=1),
        ])
        db.commit()

        # 仅 found.mp3 在 found_rel_paths 中
        count = _cleanup_missing_tracks(db, wd, {"found.mp3"})
        db.commit()

        check("清理 2 首", count == 2, f"got {count}")

        db.expire_all()
        check("found 未软删除", db.get(Track, t_found.id).deleted_at is None)
        check("miss1 已软删除", db.get(Track, t_miss1.id).deleted_at is not None)
        check("miss2 已软删除", db.get(Track, t_miss2.id).deleted_at is not None)

        items = db.query(PlaylistItem).filter(PlaylistItem.playlist_id == pl.id).all()
        check("PlaylistItem 已清理", len(items) == 0, f"left {len(items)}")


def test_cleanup_missing_tracks_keeps_soft_deleted() -> None:
    """_cleanup_missing_tracks 不重复处理已软删除的曲目"""
    print("\n=== test_cleanup_missing_tracks_keeps_soft_deleted ===")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        wd_path = _make_watch_dir(tmp_root)

        db, _eng = _make_test_db()
        user = _make_user(db)
        wd = WatchDir(path=str(wd_path), recursive=True, enabled=True)
        db.add(wd)
        db.commit()
        db.refresh(wd)

        t = Track(
            watch_dir_id=wd.id, rel_path="gone.mp3", abs_path=str(wd_path / "gone.mp3"),
            filename="gone.mp3", ext="mp3", title="gone",
            deleted_at=datetime.utcnow(),  # 已软删除
        )
        db.add(t)
        db.commit()
        db.refresh(t)

        # found_rel_paths 为空，但曲目已软删除，不应再被处理
        count = _cleanup_missing_tracks(db, wd, set())
        db.commit()

        check("不重复处理已软删除", count == 0, f"got {count}")


def main() -> int:
    print("=" * 60)
    print("1.2.1 曲目删除与库一致性 - 节点侧测试")
    print("=" * 60)

    test_resolve_inside_watch_dir()
    test_compute_file_hash()
    test_handle_track_delete_basic()
    test_handle_track_delete_file_missing()
    test_handle_track_delete_idempotent()
    test_handle_track_delete_nonexistent_track()
    test_cleanup_missing_tracks()
    test_cleanup_missing_tracks_keeps_soft_deleted()

    print()
    print("=" * 60)
    print(f"结果: {_pass} 通过 / {_fail} 失败")
    print("=" * 60)
    return 0 if _fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
