from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from eta_node.database import SessionLocal
from eta_node.models import (
    Playlist,
    PlaylistItem,
    Track,
    User,
    SYSTEM_PLAYLIST_INBOX,
)
from eta_node.versioning import bump_version, ENTITY_PLAYLISTS

logger = logging.getLogger("etamusic.plugins.local_node")


def _get_or_create_inbox(db: Session) -> Optional[Playlist]:
    pl = (
        db.query(Playlist)
        .filter(Playlist.is_system.is_(True), Playlist.name == SYSTEM_PLAYLIST_INBOX)
        .one_or_none()
    )
    if pl is None:
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


def add_tracks_to_inbox(track_ids: list[int]) -> int:
    db = SessionLocal()
    try:
        inbox = _get_or_create_inbox(db)
        if inbox is None:
            logger.warning("收集箱播放列表不存在且无法创建")
            return 0
        added = 0
        for tid in track_ids:
            track = db.get(Track, tid)
            if track is None:
                continue
            existing = (
                db.query(PlaylistItem)
                .filter(
                    PlaylistItem.playlist_id == inbox.id,
                    PlaylistItem.track_id == tid,
                )
                .one_or_none()
            )
            if existing is not None:
                continue
            max_pos = (
                db.query(PlaylistItem.position)
                .filter(PlaylistItem.playlist_id == inbox.id)
                .order_by(PlaylistItem.position.desc())
                .first()
            )
            next_pos = (max_pos[0] + 1) if max_pos else 0
            item = PlaylistItem(
                playlist_id=inbox.id,
                track_id=tid,
                position=next_pos,
            )
            db.add(item)
            added += 1
        if added > 0:
            bump_version(db, ENTITY_PLAYLISTS)
            db.commit()
        return added
    except Exception as e:
        logger.error("添加曲目到收集箱失败: %s", e, exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def find_tracks_by_paths(file_paths: list[str]) -> list[int]:
    if not file_paths:
        return []
    db = SessionLocal()
    try:
        tracks = db.query(Track).filter(Track.abs_path.in_(file_paths)).all()
        return [t.id for t in tracks]
    finally:
        db.close()
