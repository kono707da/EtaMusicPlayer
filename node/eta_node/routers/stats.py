"""播放统计与数据看板 API

- POST /api/stats/play  上报播放事件（play/skip/complete）
- GET  /api/stats/dashboard  获取统计数据看板

播放事件使用原子 SQL UPDATE，不经过任务队列（高频、低风险、需要即时响应）。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import get_current_user_dependency
from eta_node.models import (
    PlayHistory,
    Track,
    TrackStats,
    User,
    UserPlayStats,
)

logger = logging.getLogger("eta_node.routers.stats")

router = APIRouter(prefix="/api/stats", tags=["stats"])


# ---- 请求/响应模型 ----

class PlayEventRequest(BaseModel):
    """播放事件上报"""
    track_id: int
    event_type: str  # "play" | "skip" | "complete"


class PlayEventResponse(BaseModel):
    ok: bool
    message: str = ""


class DashboardResponse(BaseModel):
    """数据看板"""
    total_tracks: int
    total_play_count: int
    total_skip_count: int
    total_complete_count: int
    tracks_imported_today: int
    tracks_imported_this_week: int
    top_played_tracks: list[dict] = []
    recent_plays: list[dict] = []
    active_users: list[dict] = []


# ---- 播放事件上报 ----

@router.post("/play", response_model=PlayEventResponse)
def record_play_event(
    payload: PlayEventRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlayEventResponse:
    """上报播放事件

    event_type:
    - play: 用户开始播放
    - skip: 用户跳过
    - complete: 用户播放完成
    """
    if payload.event_type not in ("play", "skip", "complete"):
        raise HTTPException(status_code=400, detail="event_type 必须是 play/skip/complete")

    track = db.get(Track, payload.track_id)
    # 1.2.1：软删除曲目不可上报播放事件
    if track is None or track.deleted_at is not None:
        raise HTTPException(status_code=404, detail="曲目不存在")

    now = datetime.utcnow()

    # 1. 更新 TrackStats
    stats = (
        db.query(TrackStats)
        .filter(TrackStats.track_id == payload.track_id)
        .one_or_none()
    )
    if stats is None:
        # 首次播放，创建统计记录
        stats = TrackStats(
            track_id=payload.track_id,
            imported_at=track.created_at or now,
        )
        db.add(stats)
        db.flush()

    if payload.event_type == "play":
        stats.total_play_count += 1
        stats.last_played_at = now
        stats.last_played_by = user.username
    elif payload.event_type == "skip":
        stats.total_skip_count += 1
    elif payload.event_type == "complete":
        stats.total_complete_count += 1

    # 2. 更新 UserPlayStats（原子操作）
    user_stats = (
        db.query(UserPlayStats)
        .filter(
            UserPlayStats.user_id == user.id,
            UserPlayStats.track_id == payload.track_id,
        )
        .one_or_none()
    )
    if user_stats is None:
        user_stats = UserPlayStats(
            user_id=user.id,
            track_id=payload.track_id,
            first_played_at=now,
        )
        db.add(user_stats)
        db.flush()

    if payload.event_type == "play":
        user_stats.play_count += 1
        user_stats.last_played_at = now
    elif payload.event_type == "skip":
        user_stats.skip_count += 1
    elif payload.event_type == "complete":
        user_stats.complete_count += 1
        user_stats.last_played_at = now

    # 3. 记录播放历史
    history = PlayHistory(
        user_id=user.id,
        track_id=payload.track_id,
        played_at=now,
        client_info=user.username,
    )
    db.add(history)

    db.commit()
    return PlayEventResponse(ok=True, message=f"已记录 {payload.event_type} 事件")


# ---- 数据看板 ----

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> DashboardResponse:
    """获取统计数据看板"""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # 1.2.1：所有统计查询排除软删除曲目
    # 总曲目数
    total_tracks = (
        db.query(func.count(Track.id))
        .filter(Track.deleted_at.is_(None))
        .scalar() or 0
    )

    # 总播放/跳过/完成数：仅统计未软删除曲目的统计行
    total_play = (
        db.query(func.sum(TrackStats.total_play_count))
        .join(Track, TrackStats.track_id == Track.id)
        .filter(Track.deleted_at.is_(None))
        .scalar() or 0
    )
    total_skip = (
        db.query(func.sum(TrackStats.total_skip_count))
        .join(Track, TrackStats.track_id == Track.id)
        .filter(Track.deleted_at.is_(None))
        .scalar() or 0
    )
    total_complete = (
        db.query(func.sum(TrackStats.total_complete_count))
        .join(Track, TrackStats.track_id == Track.id)
        .filter(Track.deleted_at.is_(None))
        .scalar() or 0
    )

    # 今日/本周入库：基于未软删除曲子的 TrackStats
    imported_today = (
        db.query(func.count(TrackStats.track_id))
        .join(Track, TrackStats.track_id == Track.id)
        .filter(TrackStats.imported_at >= today_start, Track.deleted_at.is_(None))
        .scalar() or 0
    )
    imported_this_week = (
        db.query(func.count(TrackStats.track_id))
        .join(Track, TrackStats.track_id == Track.id)
        .filter(TrackStats.imported_at >= week_ago, Track.deleted_at.is_(None))
        .scalar() or 0
    )

    # 热门曲目（按播放次数 Top 10）
    top_tracks_q = (
        db.query(
            TrackStats.track_id,
            TrackStats.total_play_count,
            TrackStats.total_complete_count,
            Track.title,
            Track.artist,
        )
        .join(Track, TrackStats.track_id == Track.id)
        .filter(TrackStats.total_play_count > 0, Track.deleted_at.is_(None))
        .order_by(TrackStats.total_play_count.desc())
        .limit(10)
        .all()
    )
    top_played = [
        {
            "track_id": r.track_id,
            "title": r.title,
            "artist": r.artist,
            "play_count": r.total_play_count,
            "complete_count": r.total_complete_count,
        }
        for r in top_tracks_q
    ]

    # 最近播放记录（10条）：排除软删除曲目
    recent_plays_q = (
        db.query(
            PlayHistory.played_at,
            PlayHistory.track_id,
            PlayHistory.user_id,
            Track.title,
            User.username,
        )
        .join(Track, PlayHistory.track_id == Track.id)
        .join(User, PlayHistory.user_id == User.id)
        .filter(Track.deleted_at.is_(None))
        .order_by(PlayHistory.played_at.desc())
        .limit(10)
        .all()
    )
    recent_plays = [
        {
            "played_at": r.played_at.isoformat() if r.played_at else None,
            "track_id": r.track_id,
            "title": r.title,
            "username": r.username,
        }
        for r in recent_plays_q
    ]

    # 活跃用户（按播放次数 Top 5）
    active_users_q = (
        db.query(
            User.username,
            func.sum(UserPlayStats.play_count).label("plays"),
            func.sum(UserPlayStats.complete_count).label("completes"),
        )
        .join(UserPlayStats, UserPlayStats.user_id == User.id)
        .group_by(User.id, User.username)
        .order_by(text("plays DESC"))
        .limit(5)
        .all()
    )
    active_users = [
        {
            "username": r.username,
            "play_count": int(r.plays) if r.plays else 0,
            "complete_count": int(r.completes) if r.completes else 0,
        }
        for r in active_users_q
    ]

    return DashboardResponse(
        total_tracks=total_tracks,
        total_play_count=total_play,
        total_skip_count=total_skip,
        total_complete_count=total_complete,
        tracks_imported_today=imported_today,
        tracks_imported_this_week=imported_this_week,
        top_played_tracks=top_played,
        recent_plays=recent_plays,
        active_users=active_users,
    )
