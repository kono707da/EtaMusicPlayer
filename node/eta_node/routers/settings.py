"""播放完成判定配置 API

GET /api/settings/playback  读取配置（任何登录用户可读，前端需要拿这个判断）
PUT /api/settings/playback  修改配置（admin only）

配置用于前端播放器按曲目时长区分音乐/广播剧，应用不同的完成百分比：
- 时长 >= duration_threshold_seconds 视为广播剧
- 时长 <  duration_threshold_seconds 视为音乐
前端在播放进度达到对应百分比时上报 complete 事件（仅记统计，不自动切歌）。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import get_current_user_dependency, require_admin
from eta_node.models import PlaybackSettings, User


router = APIRouter(prefix="/api/settings", tags=["settings"])


# 默认值常量（与 models.py 保持一致，用于旧库无记录时的兜底）
DEFAULT_DURATION_THRESHOLD_SECONDS = 900
DEFAULT_MUSIC_COMPLETE_PERCENT = 90
DEFAULT_BROADCAST_COMPLETE_PERCENT = 70


class PlaybackSettingsOut(BaseModel):
    """播放完成配置响应"""
    duration_threshold_seconds: int
    music_complete_percent: int
    broadcast_complete_percent: int


class PlaybackSettingsUpdate(BaseModel):
    """播放完成配置更新请求

    所有字段可选，只更新传入的字段。百分比范围 1-100，时长阈值范围 60-86400 秒。
    """
    duration_threshold_seconds: int | None = Field(
        default=None, ge=60, le=86400,
        description="音乐/广播剧分界时长（秒），范围 60-86400",
    )
    music_complete_percent: int | None = Field(
        default=None, ge=1, le=100,
        description="音乐完成百分比（1-100）",
    )
    broadcast_complete_percent: int | None = Field(
        default=None, ge=1, le=100,
        description="广播剧完成百分比（1-100）",
    )


def _get_or_create_settings(db: Session) -> PlaybackSettings:
    """读取配置，不存在则用默认值创建（兜底旧库）"""
    cfg = db.get(PlaybackSettings, 1)
    if cfg is None:
        cfg = PlaybackSettings(
            id=1,
            duration_threshold_seconds=DEFAULT_DURATION_THRESHOLD_SECONDS,
            music_complete_percent=DEFAULT_MUSIC_COMPLETE_PERCENT,
            broadcast_complete_percent=DEFAULT_BROADCAST_COMPLETE_PERCENT,
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _to_out(cfg: PlaybackSettings) -> PlaybackSettingsOut:
    return PlaybackSettingsOut(
        duration_threshold_seconds=cfg.duration_threshold_seconds,
        music_complete_percent=cfg.music_complete_percent,
        broadcast_complete_percent=cfg.broadcast_complete_percent,
    )


@router.get("/playback", response_model=PlaybackSettingsOut)
def get_playback_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaybackSettingsOut:
    """读取播放完成判定配置（任何登录用户可读）"""
    cfg = _get_or_create_settings(db)
    return _to_out(cfg)


@router.put("/playback", response_model=PlaybackSettingsOut)
def update_playback_settings(
    payload: PlaybackSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> PlaybackSettingsOut:
    """更新播放完成判定配置（admin only）"""
    cfg = _get_or_create_settings(db)

    if payload.duration_threshold_seconds is not None:
        cfg.duration_threshold_seconds = payload.duration_threshold_seconds
    if payload.music_complete_percent is not None:
        cfg.music_complete_percent = payload.music_complete_percent
    if payload.broadcast_complete_percent is not None:
        cfg.broadcast_complete_percent = payload.broadcast_complete_percent

    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)
