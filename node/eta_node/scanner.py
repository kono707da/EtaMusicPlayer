"""目录扫描 + mutagen 元数据提取 + 去重入库"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile  # type: ignore
from mutagen.flac import FLAC  # type: ignore
from mutagen.id3 import ID3  # type: ignore
from mutagen.mp3 import MP3  # type: ignore
from mutagen.mp4 import MP4  # type: ignore
from mutagen.wave import WAVE  # type: ignore
from sqlalchemy.orm import Session

from eta_node.database import SessionLocal
from eta_node.models import (
    Playlist,
    PlaylistItem,
    ScanTask,
    SYSTEM_PLAYLIST_ALL,
    SYSTEM_PLAYLIST_INBOX,
    Track,
    WatchDir,
)
from eta_node.versioning import bump_version, ENTITY_TRACKS, ENTITY_PLAYLISTS


# 支持扫描的音频扩展名（小写，含点）
SUPPORTED_EXTS = {".mp3", ".flac", ".wav", ".ape", ".m4a", ".alac", ".ogg", ".opus", ".aiff"}

# 格式优先级映射
FORMAT_PRIORITY = {
    "flac": 5,
    "wav": 4,
    "ape": 4,
    "alac": 4,
    "m4a": 3,
    "mp3": 2,
    "ogg": 2,
    "opus": 2,
}


def get_format_priority(ext: str) -> int:
    """根据扩展名返回格式优先级，未知格式返回 1"""
    return FORMAT_PRIORITY.get(ext.lower().lstrip("."), 1)


def compute_quality_score(format_priority: int, bitrate: int, sample_rate: int) -> int:
    """计算音质评分：format_priority*1000000 + bitrate + sample_rate/1000"""
    return int(format_priority * 1_000_000 + (bitrate or 0) + int((sample_rate or 0) / 1000))


def _extract_metadata(file_path: str) -> dict:
    """用 mutagen 提取元数据，返回统一字段字典"""
    info: dict = {
        "title": None,
        "artist": None,
        "album": None,
        "album_artist": None,
        "track_no": None,
        "year": None,
        "genre": None,
        "duration": None,
        "bitrate": None,
        "sample_rate": None,
        "channels": None,
        "cover_embedded": False,
        "lyrics_embedded": False,
    }

    try:
        mf = MutagenFile(file_path)
    except Exception:
        return info

    if mf is None:
        return info

    try:
        # 时长与采样率/位率/声道
        try:
            if mf.info is not None:
                info["duration"] = getattr(mf.info, "length", None)
                info["bitrate"] = getattr(mf.info, "bitrate", None)
                info["sample_rate"] = getattr(mf.info, "sample_rate", None)
                info["channels"] = getattr(mf.info, "channels", None)
        except Exception:
            pass

        # 标签字段（不同格式不同 API）
        tags = getattr(mf, "tags", None)
        if tags is not None:
            def _first(*keys: str) -> Optional[str]:
                for k in keys:
                    if k in tags:
                        vals = tags[k]
                        if isinstance(vals, list):
                            if vals:
                                return str(vals[0])
                        elif vals is not None:
                            return str(vals)
                return None

            info["title"] = _first("title", "TIT2", "\xa9nam")
            info["artist"] = _first("artist", "TPE1", "\xa9ART")
            info["album"] = _first("album", "TALB", "\xa9alb")
            info["album_artist"] = _first("albumartist", "TPE2", "aART", "\xa9ART")
            info["genre"] = _first("genre", "TCON", "\xa9gen")

            trackno_raw = _first("tracknumber", "TRCK", "trkn", "\xa9trk")
            if trackno_raw:
                # 形如 "3/12" 或 "3"
                info["track_no"] = _parse_int(trackno_raw.split("/")[0])

            year_raw = _first("date", "year", "TDRC", "\xa9day")
            if year_raw:
                info["year"] = _parse_int(year_raw[:4])

        # 嵌入封面/歌词检测
        try:
            if isinstance(mf, (MP3, WAVE)):
                # MP3 和 WAV 都用 ID3 tags（APIC/USLT）
                # ID3 key 形如 "APIC:Cover" / "USLT:Lyrics"（带 desc 后缀），用 startswith 匹配
                if any(k.startswith("APIC") for k in (tags or {})):
                    info["cover_embedded"] = True
                if any(k.startswith("USLT") or k.startswith("SYLT") for k in (tags or {})):
                    info["lyrics_embedded"] = True
            elif isinstance(mf, FLAC):
                if mf.pictures:
                    info["cover_embedded"] = True
                if "lyrics" in (tags or {}):
                    info["lyrics_embedded"] = True
            elif isinstance(mf, MP4):
                covr = tags.get("covr") if tags else None
                if covr:
                    info["cover_embedded"] = True
                if "\xa9lyr" in (tags or {}):
                    info["lyrics_embedded"] = True
        except Exception:
            pass

        return info
    finally:
        # Windows 上必须显式关闭，否则文件句柄泄漏导致后续写入 Bad file descriptor
        try:
            mf.close()
        except Exception:
            pass


def _parse_int(value: str | None) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _iter_audio_files(root: str, recursive: bool):
    """遍历目录下的音频文件"""
    root_path = Path(root)
    if not root_path.exists():
        return
    if recursive:
        for dirpath, _dirs, filenames in os.walk(root_path):
            for fn in filenames:
                p = Path(dirpath) / fn
                if p.suffix.lower() in SUPPORTED_EXTS:
                    yield p
    else:
        for p in root_path.iterdir():
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                yield p


def scan_directory(watch_dir: WatchDir, db: Session) -> tuple[int, int, int]:
    """扫描单个监控目录，返回 (total_files, new_tracks, updated_tracks)

    mtime 未变则跳过；新入库的 Track 自动加入 "全部音乐" 系统播放列表。
    """
    total_files = 0
    new_tracks = 0
    updated_tracks = 0

    system_playlist = _get_or_create_system_playlist(db)

    root = watch_dir.path
    root_path = Path(root)

    for file_path in _iter_audio_files(root, watch_dir.recursive):
        total_files += 1
        try:
            rel = file_path.relative_to(root_path)
            rel_path = rel.as_posix()
        except ValueError:
            rel_path = file_path.name

        try:
            stat = file_path.stat()
        except OSError:
            continue

        ext = file_path.suffix.lower().lstrip(".")
        filename = file_path.name
        abs_path = str(file_path)
        file_size = stat.st_size
        file_mtime = stat.st_mtime

        # 查找现有记录
        existing = (
            db.query(Track)
            .filter(Track.watch_dir_id == watch_dir.id, Track.rel_path == rel_path)
            .one_or_none()
        )

        # mtime 未变跳过
        if existing is not None and existing.file_mtime is not None:
            if abs(existing.file_mtime - file_mtime) < 1e-3:
                continue

        meta = _extract_metadata(abs_path)
        format_priority = get_format_priority(ext)
        quality_score = compute_quality_score(
            format_priority, meta.get("bitrate") or 0, meta.get("sample_rate") or 0
        )

        if existing is None:
            track = Track(
                watch_dir_id=watch_dir.id,
                rel_path=rel_path,
                abs_path=abs_path,
                filename=filename,
                ext=ext,
                title=meta["title"] or filename,
                artist=meta["artist"],
                album=meta["album"],
                album_artist=meta["album_artist"],
                track_no=meta["track_no"],
                year=meta["year"],
                genre=meta["genre"],
                duration=meta["duration"],
                bitrate=meta["bitrate"],
                sample_rate=meta["sample_rate"],
                channels=meta["channels"],
                file_size=file_size,
                file_mtime=file_mtime,
                cover_embedded=meta["cover_embedded"],
                lyrics_embedded=meta["lyrics_embedded"],
                format_priority=format_priority,
                quality_score=quality_score,
            )
            db.add(track)
            db.flush()
            # 加入系统播放列表
            _add_to_system_playlist(db, system_playlist, track)
            new_tracks += 1
        else:
            existing.abs_path = abs_path
            existing.filename = filename
            existing.ext = ext
            existing.title = meta["title"] or existing.title
            existing.artist = meta["artist"]
            existing.album = meta["album"]
            existing.album_artist = meta["album_artist"]
            existing.track_no = meta["track_no"]
            existing.year = meta["year"]
            existing.genre = meta["genre"]
            existing.duration = meta["duration"]
            existing.bitrate = meta["bitrate"]
            existing.sample_rate = meta["sample_rate"]
            existing.channels = meta["channels"]
            existing.file_size = file_size
            existing.file_mtime = file_mtime
            existing.cover_embedded = meta["cover_embedded"]
            existing.lyrics_embedded = meta["lyrics_embedded"]
            existing.format_priority = format_priority
            existing.quality_score = quality_score
            updated_tracks += 1

    watch_dir.last_scanned_at = datetime.utcnow()
    # 数据变更在同一事务内递增版本号，供访问端增量同步
    if new_tracks > 0 or updated_tracks > 0:
        bump_version(db, ENTITY_TRACKS)
    if new_tracks > 0:  # 新曲目被加入系统播放列表，播放列表内容也变更
        bump_version(db, ENTITY_PLAYLISTS)
    db.commit()
    return total_files, new_tracks, updated_tracks


def _get_or_create_system_playlist(db: Session) -> Playlist:
    """获取或创建 "全部音乐" 系统播放列表"""
    pl = (
        db.query(Playlist)
        .filter(Playlist.is_system.is_(True), Playlist.name == SYSTEM_PLAYLIST_ALL)
        .one_or_none()
    )
    if pl is None:
        # 兜底：取第一个 admin 用户作为 owner
        from eta_node.models import User

        admin = db.query(User).filter(User.is_admin.is_(True)).first()
        owner_id = admin.id if admin else 1
        pl = Playlist(
            name=SYSTEM_PLAYLIST_ALL,
            owner_id=owner_id,
            is_system=True,
            description="系统自动维护：所有已扫描曲目",
        )
        db.add(pl)
        bump_version(db, ENTITY_PLAYLISTS)
        db.commit()
        db.refresh(pl)
    return pl


def _get_or_create_inbox_playlist(db: Session) -> Optional[Playlist]:
    pl = (
        db.query(Playlist)
        .filter(Playlist.is_system.is_(True), Playlist.name == SYSTEM_PLAYLIST_INBOX)
        .one_or_none()
    )
    if pl is None:
        from eta_node.models import User

        admin = db.query(User).filter(User.is_admin.is_(True)).first()
        if admin is None:
            return None
        pl = Playlist(
            name=SYSTEM_PLAYLIST_INBOX,
            owner_id=admin.id,
            is_system=True,
            description="系统自动维护：所有下载的音频",
        )
        db.add(pl)
        bump_version(db, ENTITY_PLAYLISTS)
        db.commit()
        db.refresh(pl)
    return pl


def _add_to_system_playlist(db: Session, playlist: Playlist, track: Track) -> None:
    """将曲目加入系统播放列表（去重）"""
    existing = (
        db.query(PlaylistItem)
        .filter(
            PlaylistItem.playlist_id == playlist.id,
            PlaylistItem.track_id == track.id,
        )
        .one_or_none()
    )
    if existing is not None:
        return
    # position = 当前最大 + 1
    max_pos = (
        db.query(PlaylistItem.position)
        .filter(PlaylistItem.playlist_id == playlist.id)
        .order_by(PlaylistItem.position.desc())
        .first()
    )
    next_pos = (max_pos[0] + 1) if max_pos else 0
    item = PlaylistItem(
        playlist_id=playlist.id,
        track_id=track.id,
        position=next_pos,
    )
    db.add(item)


def run_scan(scan_task_id: int, watch_dir_id: Optional[int] = None) -> None:
    """同步执行扫描任务

    watch_dir_id 为 None 时扫描所有启用的监控目录。
    """
    db = SessionLocal()
    try:
        task = db.get(ScanTask, scan_task_id)
        if task is None:
            return
        task.status = "running"
        task.started_at = datetime.utcnow()
        db.commit()

        try:
            query = db.query(WatchDir).filter(WatchDir.enabled.is_(True))
            if watch_dir_id is not None:
                query = query.filter(WatchDir.id == watch_dir_id)
            watch_dirs = query.all()

            total_all = 0
            new_all = 0
            updated_all = 0
            for wd in watch_dirs:
                t, n, u = scan_directory(wd, db)
                total_all += t
                new_all += n
                updated_all += u
                task.total_files = total_all
                task.processed_files = total_all
                task.new_tracks = new_all
                task.updated_tracks = updated_all
                db.commit()

            task.status = "completed"
            task.finished_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)[:2000]
            task.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
