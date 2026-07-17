"""节点缓存路由：供前端读取离线节点缓存 + 触发同步

端点：
- POST /api/library/refresh          触发所有在线节点增量同步
- GET  /api/cached-tracks            读取节点曲库缓存（指定 node_id 或全部）
- GET  /api/cached-playlists         读取节点播放列表缓存
- GET  /api/node-sync-states         读取各节点同步状态
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from eta_web.plugins_manager.database import get_db
from eta_web.plugins_manager.models import RemoteNode
from eta_web.node_cache.models import (
    NodeTrackCache,
    NodePlaylistCache,
    NodeSyncState,
)
from eta_web.node_cache.sync_service import sync_all_nodes

router = APIRouter(prefix="/api", tags=["node_cache"])


class TrackCacheOut(BaseModel):
    node_id: int
    track_id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    track_no: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_size: Optional[int] = None
    cover_embedded: bool = False
    lyrics_embedded: bool = False
    format_priority: int = 1
    quality_score: int = 0
    is_deleted: bool = False

    model_config = {"from_attributes": True}


class PlaylistCacheOut(BaseModel):
    node_id: int
    playlist_id: int
    name: str
    owner_id: Optional[int] = None
    is_system: bool = False
    description: Optional[str] = None
    items: list[dict] = []
    is_deleted: bool = False

    model_config = {"from_attributes": True}


class SyncStateOut(BaseModel):
    node_id: int
    entity_type: str
    last_sync_version: int
    last_synced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SyncResultOut(BaseModel):
    node_id: int
    tracks_synced: int = 0
    playlists_synced: int = 0
    skipped: bool = False
    error: Optional[str] = None


@router.post("/library/refresh", response_model=list[SyncResultOut])
def refresh_library(db: Session = Depends(get_db)) -> list[dict]:
    """触发所有在线节点的增量同步（前端进入工作台时调用）"""
    results = sync_all_nodes(db)
    return results


@router.get("/cached-tracks", response_model=list[TrackCacheOut])
def get_cached_tracks(
    node_id: Optional[int] = Query(None, description="指定节点 ID，不传则返回所有节点的缓存"),
    include_deleted: bool = Query(False, description="是否包含已标记删除的曲目"),
    q: Optional[str] = Query(None, description="搜索关键词（title/artist/album）"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """读取节点曲库缓存（供离线节点展示）"""
    query = db.query(NodeTrackCache)
    if node_id is not None:
        query = query.filter(NodeTrackCache.node_id == node_id)
    if not include_deleted:
        query = query.filter(NodeTrackCache.is_deleted.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter(
            (NodeTrackCache.title.like(like))
            | (NodeTrackCache.artist.like(like))
            | (NodeTrackCache.album.like(like))
        )
    rows = query.order_by(NodeTrackCache.artist, NodeTrackCache.album, NodeTrackCache.track_no).all()
    return [
        {
            "node_id": r.node_id,
            "track_id": r.track_id,
            "title": r.title,
            "artist": r.artist,
            "album": r.album,
            "album_artist": r.album_artist,
            "track_no": r.track_no,
            "year": r.year,
            "genre": r.genre,
            "duration": r.duration,
            "bitrate": r.bitrate,
            "sample_rate": r.sample_rate,
            "channels": r.channels,
            "file_size": r.file_size,
            "cover_embedded": r.cover_embedded,
            "lyrics_embedded": r.lyrics_embedded,
            "format_priority": r.format_priority,
            "quality_score": r.quality_score,
            "is_deleted": r.is_deleted,
        }
        for r in rows
    ]


@router.get("/cached-playlists", response_model=list[PlaylistCacheOut])
def get_cached_playlists(
    node_id: Optional[int] = Query(None, description="指定节点 ID，不传则返回所有节点的缓存"),
    include_deleted: bool = Query(False, description="是否包含已标记删除的播放列表"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """读取节点播放列表缓存"""
    query = db.query(NodePlaylistCache)
    if node_id is not None:
        query = query.filter(NodePlaylistCache.node_id == node_id)
    if not include_deleted:
        query = query.filter(NodePlaylistCache.is_deleted.is_(False))
    rows = query.order_by(NodePlaylistCache.node_id, NodePlaylistCache.playlist_id).all()
    return [
        {
            "node_id": r.node_id,
            "playlist_id": r.playlist_id,
            "name": r.name,
            "owner_id": r.owner_id,
            "is_system": r.is_system,
            "description": r.description,
            "items": json.loads(r.items_json) if r.items_json else [],
            "is_deleted": r.is_deleted,
        }
        for r in rows
    ]


@router.get("/node-sync-states", response_model=list[SyncStateOut])
def get_sync_states(
    node_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    """读取各节点的同步状态"""
    query = db.query(NodeSyncState)
    if node_id is not None:
        query = query.filter(NodeSyncState.node_id == node_id)
    rows = query.all()
    return [
        {
            "node_id": r.node_id,
            "entity_type": r.entity_type,
            "last_sync_version": r.last_sync_version,
            "last_synced_at": r.last_synced_at,
        }
        for r in rows
    ]
