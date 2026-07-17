"""数据增量同步路由：供访问端拉取曲库/播放列表的变更

访问端通过 GET /api/version 获取 data_versions 后，
与本地 node_sync_state.last_sync_version 比对，
若落后则调用本模块的 /api/{entity}/changes?since_version=N 拉取增量。

增量原理：
- Track/Playlist 有 version_stamp 列，记录该行最后一次变更时的版本号
- bump_version 在递增 data_versions.version 的同时，给 session 中 dirty/new 的对象打戳
- 增量查询 WHERE version_stamp > since_version，只返回真正变更的记录
- 软删除的记录（deleted_at != null）也通过 version_stamp 触发，会被增量返回

响应格式：
{
  "entity_type": "tracks" | "playlists",
  "since_version": N,
  "current_version": M,
  "changes": [
    { ...完整字段..., "deleted": false },
    { "id": 123, "deleted": true, "updated_at": "..." }
  ]
}
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.models import Playlist, PlaylistItem, Track
from eta_node.versioning import get_version, ENTITY_TRACKS, ENTITY_PLAYLISTS

router = APIRouter(prefix="/api", tags=["data_sync"])


class ChangesResponse(BaseModel):
    entity_type: str
    since_version: int
    current_version: int
    changes: list[dict]


@router.get("/tracks/changes", response_model=ChangesResponse)
def get_tracks_changes(
    since_version: int = Query(0, ge=0, description="上次同步的版本号，0 表示全量拉取"),
    db: Session = Depends(get_db),
) -> dict:
    """拉取曲库增量变更

    since_version=0 时全量拉取所有未删除曲目；
    since_version>0 时只返回 version_stamp > since_version 的记录（含软删除）。
    """
    current_version = get_version(db, ENTITY_TRACKS)

    if since_version == 0:
        # 全量：所有未删除曲目
        tracks = db.query(Track).filter(Track.deleted_at.is_(None)).all()
    else:
        # 增量：version_stamp > since_version（含软删除的，因为软删除时也会打戳）
        tracks = db.query(Track).filter(Track.version_stamp > since_version).all()

    changes = []
    for t in tracks:
        if t.deleted_at is not None:
            changes.append({
                "id": t.id,
                "deleted": True,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            })
        else:
            changes.append({
                "id": t.id,
                "deleted": False,
                "watch_dir_id": t.watch_dir_id,
                "rel_path": t.rel_path,
                "filename": t.filename,
                "ext": t.ext,
                "title": t.title,
                "artist": t.artist,
                "album": t.album,
                "album_artist": t.album_artist,
                "track_no": t.track_no,
                "year": t.year,
                "genre": t.genre,
                "duration": t.duration,
                "bitrate": t.bitrate,
                "sample_rate": t.sample_rate,
                "channels": t.channels,
                "file_size": t.file_size,
                "cover_embedded": t.cover_embedded,
                "lyrics_embedded": t.lyrics_embedded,
                "format_priority": t.format_priority,
                "quality_score": t.quality_score,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            })

    return {
        "entity_type": ENTITY_TRACKS,
        "since_version": since_version,
        "current_version": current_version,
        "changes": changes,
    }


@router.get("/playlists/changes", response_model=ChangesResponse)
def get_playlists_changes(
    since_version: int = Query(0, ge=0, description="上次同步的版本号，0 表示全量拉取"),
    db: Session = Depends(get_db),
) -> dict:
    """拉取播放列表增量变更（含每个播放列表的曲目成员）"""
    current_version = get_version(db, ENTITY_PLAYLISTS)

    if since_version == 0:
        playlists = db.query(Playlist).filter(Playlist.deleted_at.is_(None)).all()
    else:
        playlists = db.query(Playlist).filter(Playlist.version_stamp > since_version).all()

    changes = []
    for pl in playlists:
        if pl.deleted_at is not None:
            changes.append({
                "id": pl.id,
                "deleted": True,
                "updated_at": pl.updated_at.isoformat() if pl.updated_at else None,
            })
        else:
            items = (
                db.query(PlaylistItem)
                .filter(PlaylistItem.playlist_id == pl.id)
                .order_by(PlaylistItem.position)
                .all()
            )
            changes.append({
                "id": pl.id,
                "deleted": False,
                "name": pl.name,
                "owner_id": pl.owner_id,
                "is_system": pl.is_system,
                "description": pl.description,
                "updated_at": pl.updated_at.isoformat() if pl.updated_at else None,
                "items": [{"track_id": it.track_id, "position": it.position} for it in items],
            })

    return {
        "entity_type": ENTITY_PLAYLISTS,
        "since_version": since_version,
        "current_version": current_version,
        "changes": changes,
    }
