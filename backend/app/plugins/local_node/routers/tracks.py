"""曲目路由：列表、详情、流式（Range 支持）、封面、歌词"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from mutagen import File as MutagenFile  # type: ignore
from mutagen.flac import FLAC  # type: ignore
from mutagen.id3 import APIC  # type: ignore
from mutagen.mp4 import MP4  # type: ignore
from sqlalchemy.orm import Session

from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import get_current_user_dependency, get_user_from_query_token
from app.plugins.local_node.models import Playlist, PlaylistItem, PlaylistPermission, Track, User
from app.plugins.local_node.schemas import PaginatedTracks, TrackOut


router = APIRouter(prefix="/api/tracks", tags=["tracks"])


# Content-Type 映射
CONTENT_TYPES = {
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "wav": "audio/wav",
    "ape": "audio/ape",
    "m4a": "audio/mp4",
    "alac": "audio/mp4",
    "ogg": "audio/ogg",
    "opus": "audio/opus",
    "aiff": "audio/aiff",
}


def _visible_playlist_ids(db: Session, user: User) -> set[int]:
    """返回当前用户可见的播放列表 ID 集合（拥有 + 被授权 + 系统）"""
    ids: set[int] = set()
    owned = db.query(Playlist.id).filter(Playlist.owner_id == user.id).all()
    for (pid,) in owned:
        ids.add(pid)
    granted = (
        db.query(PlaylistPermission.playlist_id)
        .filter(PlaylistPermission.user_id == user.id)
        .all()
    )
    for (pid,) in granted:
        ids.add(pid)
    system = db.query(Playlist.id).filter(Playlist.is_system.is_(True)).all()
    for (pid,) in system:
        ids.add(pid)
    return ids


def _check_track_visible(db: Session, track_id: int, user: User) -> Track:
    """校验当前用户是否有权访问该曲目"""
    track = db.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="曲目不存在")
    # admin 可见全部
    if user.is_admin:
        return track
    visible_pids = _visible_playlist_ids(db, user)
    exists = (
        db.query(PlaylistItem.id)
        .join(PlaylistItem.playlist)
        .filter(
            PlaylistItem.track_id == track_id,
            PlaylistItem.playlist_id.in_(visible_pids),
        )
        .first()
    )
    if not exists:
        raise HTTPException(status_code=403, detail="无权访问该曲目")
    return track


@router.get("", response_model=PaginatedTracks)
def list_tracks(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=500),
    q: Optional[str] = None,
    playlist_id: Optional[int] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PaginatedTracks:
    """曲目分页列表（按用户权限过滤）"""
    visible_pids = _visible_playlist_ids(db, user)

    query = db.query(Track)
    if not user.is_admin or playlist_id is not None:
        # 限制到可见播放列表的曲目
        if playlist_id is not None:
            if playlist_id not in visible_pids and not user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问该播放列表")
            track_ids = (
                db.query(PlaylistItem.track_id)
                .filter(PlaylistItem.playlist_id == playlist_id)
                .distinct()
            )
            query = query.filter(Track.id.in_(track_ids))
        else:
            track_ids = (
                db.query(PlaylistItem.track_id)
                .filter(PlaylistItem.playlist_id.in_(visible_pids))
                .distinct()
            )
            query = query.filter(Track.id.in_(track_ids))

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Track.title.ilike(like))
            | (Track.artist.ilike(like))
            | (Track.album.ilike(like))
        )
    if artist:
        query = query.filter(Track.artist.ilike(f"%{artist}%"))
    if album:
        query = query.filter(Track.album.ilike(f"%{album}%"))

    total = query.count()
    items = (
        query.order_by(Track.artist, Track.album, Track.track_no)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return PaginatedTracks(
        total=total, page=page, size=size, items=[TrackOut.model_validate(t) for t in items]
    )


@router.get("/{track_id}", response_model=TrackOut)
def get_track(
    track_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> TrackOut:
    """曲目详情"""
    track = _check_track_visible(db, track_id, user)
    return TrackOut.model_validate(track)


@router.get("/{track_id}/stream")
def stream_track(
    track_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_query_token),
):
    """流式分发，支持 HTTP Range 断点续传

    JWT 通过 query 参数 ?token= 传递。
    """
    track = _check_track_visible(db, track_id, user)
    file_path = Path(track.abs_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    file_size = file_path.stat().st_size
    content_type = CONTENT_TYPES.get(track.ext.lower(), "application/octet-stream")

    range_header = request.headers.get("range")
    if range_header:
        # 解析 bytes=start-end
        start, end = _parse_range(range_header, file_size)
        length = end - start + 1

        def iter_chunks():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = length
                chunk_size = 64 * 1024
                while remaining > 0:
                    read = min(chunk_size, remaining)
                    data = f.read(read)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": content_type,
            "Cache-Control": "no-cache",
        }
        return StreamingResponse(
            iter_chunks(),
            status_code=206,
            headers=headers,
            media_type=content_type,
        )
    else:
        # 全量返回
        def iter_all():
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(64 * 1024)
                    if not data:
                        break
                    yield data

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": content_type,
        }
        return StreamingResponse(
            iter_all(),
            status_code=200,
            headers=headers,
            media_type=content_type,
        )


def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
    """解析 Range 头，返回 (start, end)，end 闭区间"""
    try:
        unit, ranges = range_header.split("=")
        if unit.strip().lower() != "bytes":
            raise ValueError
        start_str, end_str = ranges.split("-")
        start = int(start_str) if start_str.strip() else 0
        end = int(end_str) if end_str.strip() else file_size - 1
        if end >= file_size:
            end = file_size - 1
        if start > end or start < 0:
            raise ValueError
        return start, end
    except (ValueError, IndexError):
        from fastapi import HTTPException, status as _status
        raise HTTPException(
            status_code=_status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail="无效的 Range 头",
            headers={"Content-Range": f"bytes */{file_size}"},
        )


@router.get("/{track_id}/cover")
def get_cover(
    track_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """提取并返回嵌入封面图"""
    track = _check_track_visible(db, track_id, user)
    if not track.cover_embedded:
        raise HTTPException(status_code=404, detail="无嵌入封面")
    try:
        mf = MutagenFile(track.abs_path)
    except Exception:
        raise HTTPException(status_code=500, detail="读取文件失败")

    image_bytes: Optional[bytes] = None
    mime = "image/jpeg"
    try:
        if mf is not None:
            # FLAC：pictures 属性
            pics = getattr(mf, "pictures", None)
            if pics:
                image_bytes = pics[0].data
                mime = getattr(pics[0], "mime", mime) or mime
            tags = getattr(mf, "tags", None)
            # MP3 ID3 APIC
            if image_bytes is None and tags is not None:
                for k in tags:
                    if k.startswith("APIC"):
                        apic = tags[k]
                        if hasattr(apic, "data"):
                            image_bytes = apic.data
                            mime = getattr(apic, "mime", mime) or mime
                            break
            # MP4 covr
            if image_bytes is None and isinstance(mf, MP4):
                covr = mf.tags.get("covr") if mf.tags else None
                if covr:
                    image_bytes = bytes(covr[0])
                    mime = "image/png" if image_bytes[:4] == b"\x89PNG" else "image/jpeg"
    except Exception:
        raise HTTPException(status_code=500, detail="提取封面失败")

    if not image_bytes:
        raise HTTPException(status_code=404, detail="未找到封面数据")

    return Response(content=image_bytes, media_type=mime)


@router.get("/{track_id}/lyrics")
def get_lyrics(
    track_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """返回歌词文本"""
    track = _check_track_visible(db, track_id, user)
    if not track.lyrics_embedded:
        raise HTTPException(status_code=404, detail="无嵌入歌词")
    try:
        mf = MutagenFile(track.abs_path)
    except Exception:
        raise HTTPException(status_code=500, detail="读取文件失败")

    lyrics: Optional[str] = None
    try:
        if mf is not None:
            tags = getattr(mf, "tags", None)
            if tags is not None:
                # MP3 USLT
                for k in tags:
                    if k.startswith("USLT"):
                        lyrics = str(tags[k].text[0]) if getattr(tags[k], "text", None) else ""
                        break
                if lyrics is None and "lyrics" in tags:  # FLAC
                    v = tags["lyrics"]
                    lyrics = v[0] if isinstance(v, list) else str(v)
                if lyrics is None and "\xa9lyr" in tags:  # MP4
                    v = tags["\xa9lyr"]
                    lyrics = v[0] if isinstance(v, list) else str(v)
    except Exception:
        raise HTTPException(status_code=500, detail="提取歌词失败")

    if not lyrics:
        raise HTTPException(status_code=404, detail="未找到歌词")
    return {"lyrics": lyrics}
