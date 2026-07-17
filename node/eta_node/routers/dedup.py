"""去重配置、检测、查看重复组"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.dedup import DEDUP_FIELDS_AVAILABLE, detect_duplicates, get_config, parse_fields
from eta_node.deps import get_current_user_dependency, require_admin
from eta_node.models import Track, User
from eta_node.schemas import DedupConfigOut, DedupConfigUpdate, DedupGroup, TrackOut


router = APIRouter(prefix="/api/dedup", tags=["dedup"])


# 内存缓存上次检测结果
_last_result: list[dict] = []


def _config_to_out(cfg) -> DedupConfigOut:
    return DedupConfigOut(
        id=cfg.id,
        fields=parse_fields(cfg),
        duration_tolerance=cfg.duration_tolerance,
        enabled=cfg.enabled,
    )


@router.get("/config", response_model=DedupConfigOut)
def get_dedup_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> DedupConfigOut:
    """获取当前去重配置"""
    cfg = get_config(db)
    return _config_to_out(cfg)


@router.put("/config", response_model=DedupConfigOut)
def update_dedup_config(
    payload: DedupConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> DedupConfigOut:
    """更新去重配置（admin）"""
    cfg = get_config(db)
    if payload.fields is not None:
        # 校验字段合法性
        invalid = [f for f in payload.fields if f not in DEDUP_FIELDS_AVAILABLE]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的去重字段: {invalid}，可选: {DEDUP_FIELDS_AVAILABLE}",
            )
        cfg.fields = json.dumps(payload.fields)
    if payload.duration_tolerance is not None:
        if payload.duration_tolerance < 0:
            raise HTTPException(status_code=400, detail="duration_tolerance 必须 >= 0")
        cfg.duration_tolerance = payload.duration_tolerance
    if payload.enabled is not None:
        cfg.enabled = payload.enabled
    db.commit()
    db.refresh(cfg)
    return _config_to_out(cfg)


@router.post("/detect", response_model=list[DedupGroup])
def detect_now(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> list[DedupGroup]:
    """立即检测，返回重复组"""
    global _last_result
    raw_groups = detect_duplicates(db)
    _last_result = raw_groups
    return _build_groups(db, raw_groups)


@router.get("/groups", response_model=list[DedupGroup])
def get_last_groups(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> list[DedupGroup]:
    """上次检测结果（缓存）"""
    return _build_groups(db, _last_result)


def _build_groups(db: Session, raw_groups: list[dict]) -> list[DedupGroup]:
    """构造带 TrackOut 的重复组列表

    1.2.1：双重保险，再次过滤软删除曲目，避免外部传入的 ids 包含已删除项。
    """
    result: list[DedupGroup] = []
    for g in raw_groups:
        ids = g.get("track_ids", [])
        if not ids:
            continue
        tracks = (
            db.query(Track)
            .filter(Track.id.in_(ids), Track.deleted_at.is_(None))
            .all()
        )
        # 仅保留实际未软删除的 track_id，保证 track_ids 与 tracks 一致
        valid_ids = [t.id for t in tracks]
        result.append(
            DedupGroup(
                group_key=g.get("group_key", ""),
                track_ids=valid_ids,
                tracks=[TrackOut.model_validate(t) for t in tracks],
            )
        )
    return result
