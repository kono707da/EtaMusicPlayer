"""音质升级检测（按 bitrate/sample_rate/格式优先级）"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from eta_node.models import PlaylistItem, Track
from eta_node.versioning import bump_version, ENTITY_PLAYLISTS


DURATION_TOLERANCE = 2.0  # 同曲判定时长容差（秒）


def _is_same_song(a: Track, b: Track, tol: float = DURATION_TOLERANCE) -> bool:
    """判断两首是否为同一曲目：title+album+artist 匹配，duration 容差内"""
    if not a.title or not b.title:
        return False
    if (a.title or "").strip().lower() != (b.title or "").strip().lower():
        return False
    if (a.album or "").strip().lower() != (b.album or "").strip().lower():
        return False
    if (a.artist or "").strip().lower() != (b.artist or "").strip().lower():
        return False
    # duration 校验
    if a.duration is not None and b.duration is not None:
        if abs(a.duration - b.duration) > tol:
            return False
    return True


def find_upgrades_in_playlist(db: Session, playlist_id: int) -> list[dict]:
    """检测播放列表内每个 track 的音质升级候选

    找出全库中与其"同曲"但 quality_score 更高的候选，
    返回 {current_track_id, candidates: [...], best_candidate_id}
    """
    items = (
        db.query(PlaylistItem)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .all()
    )
    current_track_ids = {it.track_id for it in items}

    all_tracks = db.query(Track).all()
    # 按 (title_lower, album_lower, artist_lower) 建立索引
    index: dict = {}
    for t in all_tracks:
        if not t.title:
            continue
        key = (
            t.title.strip().lower(),
            (t.album or "").strip().lower(),
            (t.artist or "").strip().lower(),
        )
        index.setdefault(key, []).append(t)

    results: list[dict] = []
    for it in items:
        current = db.get(Track, it.track_id)
        if current is None or not current.title:
            continue
        key = (
            current.title.strip().lower(),
            (current.album or "").strip().lower(),
            (current.artist or "").strip().lower(),
        )
        same_songs = index.get(key, [])
        # duration 二次过滤
        candidates = [
            t for t in same_songs
            if t.id != current.id and _is_same_song(current, t)
            and t.quality_score > current.quality_score
        ]
        if not candidates:
            continue
        candidates.sort(key=lambda x: x.quality_score, reverse=True)
        best = candidates[0]
        results.append(
            {
                "current_track_id": current.id,
                "candidates": [c.id for c in candidates],
                "best_candidate_id": best.id,
            }
        )
    return results


def replace_in_playlist(
    db: Session, playlist_id: int, old_track_id: int, new_track_id: int
) -> bool:
    """仅修改 PlaylistItem 的 track_id 指向，保留 position 和 added_at，不删原文件"""
    item = (
        db.query(PlaylistItem)
        .filter(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.track_id == old_track_id,
        )
        .one_or_none()
    )
    if item is None:
        return False
    # 确认新曲目存在
    new_track = db.get(Track, new_track_id)
    if new_track is None:
        return False
    # 防止重复（若新曲目已在列表中，则直接删除旧条目）
    existing_new = (
        db.query(PlaylistItem)
        .filter(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.track_id == new_track_id,
        )
        .one_or_none()
    )
    if existing_new is not None:
        db.delete(item)
        bump_version(db, ENTITY_PLAYLISTS)
        db.commit()
        return True
    item.track_id = new_track_id
    bump_version(db, ENTITY_PLAYLISTS)
    db.commit()
    return True
