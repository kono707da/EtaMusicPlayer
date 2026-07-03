"""音质升级检测与替换"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import get_current_user_dependency
from app.plugins.local_node.models import Playlist, Track, User
from app.plugins.local_node.quality import find_upgrades_in_playlist, replace_in_playlist
from app.plugins.local_node.schemas import ReplaceRequest, TrackOut, UpgradeCandidate


router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.post("/upgrades/{playlist_id}", response_model=list[UpgradeCandidate])
def detect_upgrades(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> list[UpgradeCandidate]:
    """检测该播放列表内的音质升级候选"""
    pl = db.get(Playlist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    raw = find_upgrades_in_playlist(db, playlist_id)
    result: list[UpgradeCandidate] = []
    for item in raw:
        cands = db.query(Track).filter(Track.id.in_(item["candidates"])).all()
        result.append(
            UpgradeCandidate(
                current_track_id=item["current_track_id"],
                candidates=[TrackOut.model_validate(c) for c in cands],
                best_candidate_id=item.get("best_candidate_id"),
            )
        )
    return result


@router.post("/replace", response_model=dict)
def replace_track(
    payload: ReplaceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> dict:
    """执行替换：将播放列表中 old_track_id 指向 new_track_id"""
    pl = db.get(Playlist, payload.playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    ok = replace_in_playlist(db, payload.playlist_id, payload.old_track_id, payload.new_track_id)
    if not ok:
        raise HTTPException(status_code=400, detail="替换失败：曲目不在该播放列表或新曲目不存在")
    return {"success": True}
