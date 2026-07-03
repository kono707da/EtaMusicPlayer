"""播放列表粒度授权（admin）"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import require_admin
from app.plugins.local_node.models import Playlist, PlaylistItem, PlaylistPermission, User
from app.plugins.local_node.schemas import PermissionCreate, PermissionOut, PlaylistOut


router = APIRouter(prefix="/api", tags=["permissions"])


def _to_out(p: PlaylistPermission) -> PermissionOut:
    return PermissionOut(
        id=p.id,
        playlist_id=p.playlist_id,
        user_id=p.user_id,
        granted_at=p.granted_at,
        granted_by=p.granted_by,
    )


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    playlist_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> list[PermissionOut]:
    """查询授权关系（可按 playlist_id 或 user_id 过滤）"""
    q = db.query(PlaylistPermission)
    if playlist_id is not None:
        q = q.filter(PlaylistPermission.playlist_id == playlist_id)
    if user_id is not None:
        q = q.filter(PlaylistPermission.user_id == user_id)
    perms = q.order_by(PlaylistPermission.id).all()
    return [_to_out(p) for p in perms]


@router.post("/permissions", response_model=PermissionOut, status_code=201)
def grant_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> PermissionOut:
    """授权用户访问播放列表"""
    pl = db.get(Playlist, payload.playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    target = db.get(User, payload.user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    existing = (
        db.query(PlaylistPermission)
        .filter(
            PlaylistPermission.playlist_id == payload.playlist_id,
            PlaylistPermission.user_id == payload.user_id,
        )
        .one_or_none()
    )
    if existing is not None:
        return _to_out(existing)
    perm = PlaylistPermission(
        playlist_id=payload.playlist_id,
        user_id=payload.user_id,
        granted_by=user.id,
    )
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return _to_out(perm)


@router.delete("/permissions/{permission_id}", status_code=204)
def revoke_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """撤销授权"""
    perm = db.get(PlaylistPermission, permission_id)
    if perm is None:
        raise HTTPException(status_code=404, detail="授权记录不存在")
    db.delete(perm)
    db.commit()


@router.get("/users/{user_id}/playlists", response_model=list[PlaylistOut])
def user_granted_playlists(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> list[PlaylistOut]:
    """该用户被授权的播放列表"""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    perms = (
        db.query(PlaylistPermission)
        .filter(PlaylistPermission.user_id == user_id)
        .all()
    )
    pl_ids = [p.playlist_id for p in perms]
    if not pl_ids:
        return []
    playlists = db.query(Playlist).filter(Playlist.id.in_(pl_ids)).all()
    out: list[PlaylistOut] = []
    for pl in playlists:
        count = (
            db.query(PlaylistItem)
            .filter(PlaylistItem.playlist_id == pl.id)
            .count()
        )
        out.append(
            PlaylistOut(
                id=pl.id,
                name=pl.name,
                owner_id=pl.owner_id,
                is_system=pl.is_system,
                description=pl.description,
                created_at=pl.created_at,
                updated_at=pl.updated_at,
                track_count=count,
            )
        )
    return out
