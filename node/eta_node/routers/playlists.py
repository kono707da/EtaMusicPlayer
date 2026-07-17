"""播放列表路由：CRUD、添加/移除曲目、系统列表、重排序"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import get_current_user_dependency
from eta_node.models import (
    Playlist,
    PlaylistItem,
    PlaylistPermission,
    Track,
    User,
)
from eta_node.schemas import (
    AddTracksRequest,
    PlaylistCreate,
    PlaylistDetail,
    PlaylistItemOut,
    PlaylistOut,
    PlaylistUpdate,
    ReorderRequest,
    TrackOut,
)
from eta_node.versioning import bump_and_stamp, bump_version, ENTITY_PLAYLISTS


router = APIRouter(prefix="/api/playlists", tags=["playlists"])


def _visible_playlists(db: Session, user: User) -> list[Playlist]:
    """返回当前用户可见的播放列表（排除软删除）"""
    ids: set[int] = set()
    owned = (
        db.query(Playlist.id)
        .filter(Playlist.owner_id == user.id, Playlist.deleted_at.is_(None))
        .all()
    )
    for (pid,) in owned:
        ids.add(pid)
    granted = (
        db.query(PlaylistPermission.playlist_id)
        .join(Playlist, PlaylistPermission.playlist_id == Playlist.id)
        .filter(
            PlaylistPermission.user_id == user.id,
            Playlist.deleted_at.is_(None),
        )
        .all()
    )
    for (pid,) in granted:
        ids.add(pid)
    system = (
        db.query(Playlist.id)
        .filter(Playlist.is_system.is_(True), Playlist.deleted_at.is_(None))
        .all()
    )
    for (pid,) in system:
        ids.add(pid)
    if not ids:
        return []
    return (
        db.query(Playlist)
        .filter(Playlist.id.in_(ids), Playlist.deleted_at.is_(None))
        .order_by(Playlist.name)
        .all()
    )


def _can_view_playlist(db: Session, playlist: Playlist, user: User) -> bool:
    """是否可查看该播放列表

    - admin 全可见（仅未软删除）
    - 自定义列表：所有者或被授权用户
    - 系统列表：所有登录用户可见
    """
    if playlist.deleted_at is not None:
        return False
    if user.is_admin:
        return True
    if playlist.owner_id == user.id:
        return True
    if playlist.is_system:
        return True
    exists = (
        db.query(PlaylistPermission.id)
        .filter(
            PlaylistPermission.playlist_id == playlist.id,
            PlaylistPermission.user_id == user.id,
        )
        .first()
    )
    return exists is not None


def _can_edit_playlist(db: Session, playlist: Playlist, user: User) -> bool:
    """是否可修改该播放列表成员

    - admin 全可改
    - 自定义列表：所有者或被授权用户（本期保持与查看相同语义）
    - 系统列表：仅 admin 可改成员（普通用户不可增删曲目、不可重排序）
    - 软删除列表：任何人都不可编辑
    """
    if playlist.deleted_at is not None:
        return False
    if user.is_admin:
        return True
    if playlist.is_system:
        # 普通用户不可改系统列表成员
        return False
    if playlist.owner_id == user.id:
        return True
    exists = (
        db.query(PlaylistPermission.id)
        .filter(
            PlaylistPermission.playlist_id == playlist.id,
            PlaylistPermission.user_id == user.id,
        )
        .first()
    )
    return exists is not None


# 旧名保留以向后兼容（其它模块可能引用），实际语义等于 _can_view_playlist
def _can_access_playlist(db: Session, playlist: Playlist, user: User) -> bool:
    """已废弃：使用 _can_view_playlist / _can_edit_playlist 拆分"""
    return _can_view_playlist(db, playlist, user)


def _playlist_to_out(db: Session, p: Playlist) -> PlaylistOut:
    count = db.query(PlaylistItem).filter(PlaylistItem.playlist_id == p.id).count()
    return PlaylistOut(
        id=p.id,
        name=p.name,
        owner_id=p.owner_id,
        is_system=p.is_system,
        description=p.description,
        created_at=p.created_at,
        updated_at=p.updated_at,
        track_count=count,
    )


@router.get("", response_model=list[PlaylistOut])
def list_playlists(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> list[PlaylistOut]:
    """当前用户可见的播放列表"""
    playlists = _visible_playlists(db, user)
    return [_playlist_to_out(db, p) for p in playlists]


@router.post("", response_model=PlaylistOut, status_code=201)
def create_playlist(
    payload: PlaylistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaylistOut:
    """创建播放列表"""
    pl = Playlist(
        name=payload.name,
        owner_id=user.id,
        is_system=False,
        description=payload.description,
    )
    db.add(pl)
    bump_version(db, ENTITY_PLAYLISTS)
    db.commit()
    db.refresh(pl)
    return _playlist_to_out(db, pl)


@router.get("/{playlist_id}", response_model=PlaylistDetail)
def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaylistDetail:
    """播放列表详情含曲目（排除软删除曲目）"""
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.deleted_at is not None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if not _can_view_playlist(db, pl, user):
        raise HTTPException(status_code=403, detail="无权访问该播放列表")

    items = (
        db.query(PlaylistItem)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.position)
        .all()
    )
    item_outs = []
    for it in items:
        track = db.get(Track, it.track_id)
        # 跳过软删除曲目的 track 信息（保留 PlaylistItem 行，但 track=None 让前端隐藏）
        if track is not None and track.deleted_at is not None:
            track_out = None
        else:
            track_out = TrackOut.model_validate(track) if track else None
        item_outs.append(
            PlaylistItemOut(
                id=it.id,
                track_id=it.track_id,
                position=it.position,
                added_at=it.added_at,
                track=track_out,
            )
        )
    out = _playlist_to_out(db, pl)
    return PlaylistDetail(**out.model_dump(), items=item_outs)


@router.put("/{playlist_id}", response_model=PlaylistOut)
def update_playlist(
    playlist_id: int,
    payload: PlaylistUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaylistOut:
    """更新播放列表（系统列表只改描述）"""
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.deleted_at is not None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    # 修改元信息（名称/描述）使用查看权限即可（向后兼容），但软删除列表不可改
    if not _can_view_playlist(db, pl, user):
        raise HTTPException(status_code=403, detail="无权操作")
    if pl.is_system:
        # 系统列表只允许 admin 改描述
        if not user.is_admin and payload.description is not None:
            raise HTTPException(status_code=403, detail="系统列表仅管理员可改描述")
        if payload.description is not None:
            pl.description = payload.description
        if payload.name is not None and payload.name != pl.name:
            raise HTTPException(status_code=400, detail="系统列表名称不可修改")
    else:
        if payload.name is not None:
            pl.name = payload.name
        if payload.description is not None:
            pl.description = payload.description
    bump_and_stamp(db, ENTITY_PLAYLISTS, [pl])
    db.commit()
    db.refresh(pl)
    return _playlist_to_out(db, pl)


@router.delete("/{playlist_id}", status_code=204)
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """删除播放列表（系统列表禁止删除，需可编辑权限）"""
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.deleted_at is not None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if pl.is_system:
        raise HTTPException(status_code=400, detail="系统列表不可删除")
    if not _can_edit_playlist(db, pl, user):
        raise HTTPException(status_code=403, detail="无权操作")
    pl.deleted_at = datetime.utcnow()
    bump_and_stamp(db, ENTITY_PLAYLISTS, [pl])
    db.commit()


@router.post("/{playlist_id}/tracks", response_model=PlaylistOut)
def add_tracks(
    playlist_id: int,
    payload: AddTracksRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaylistOut:
    """批量添加曲目到播放列表（拒绝已软删除曲目）"""
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.deleted_at is not None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if not _can_edit_playlist(db, pl, user):
        raise HTTPException(status_code=403, detail="无权操作")

    # 当前最大 position
    max_pos = (
        db.query(PlaylistItem.position)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.position.desc())
        .first()
    )
    next_pos = (max_pos[0] + 1) if max_pos else 0

    existing_ids = {
        tid
        for (tid,) in db.query(PlaylistItem.track_id)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .all()
    }
    added = 0
    skipped_deleted = 0
    for tid in payload.track_ids:
        if tid in existing_ids:
            continue
        track = db.get(Track, tid)
        # 拒绝添加软删除曲目
        if track is None or track.deleted_at is not None:
            skipped_deleted += 1
            continue
        item = PlaylistItem(
            playlist_id=playlist_id,
            track_id=tid,
            position=next_pos,
        )
        db.add(item)
        next_pos += 1
        added += 1
    if added > 0:
        pl.updated_at = datetime.utcnow()
        bump_and_stamp(db, ENTITY_PLAYLISTS, [pl])
    db.commit()
    db.refresh(pl)
    return _playlist_to_out(db, pl)


@router.delete("/{playlist_id}/tracks", response_model=PlaylistOut)
def remove_tracks(
    playlist_id: int,
    payload: AddTracksRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaylistOut:
    """批量移除曲目（需可编辑权限）"""
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.deleted_at is not None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if not _can_edit_playlist(db, pl, user):
        raise HTTPException(status_code=403, detail="无权操作")

    db.query(PlaylistItem).filter(
        PlaylistItem.playlist_id == playlist_id,
        PlaylistItem.track_id.in_(payload.track_ids),
    ).delete(synchronize_session=False)
    # 播放列表内容变更，需手动 touch pl 对象使其进入 dirty 并被 bump_version 打戳
    pl.updated_at = datetime.utcnow()
    bump_and_stamp(db, ENTITY_PLAYLISTS, [pl])
    db.commit()
    db.refresh(pl)
    return _playlist_to_out(db, pl)


@router.post("/{playlist_id}/reorder", response_model=PlaylistOut)
def reorder_tracks(
    playlist_id: int,
    payload: ReorderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
) -> PlaylistOut:
    """调整曲目顺序（需可编辑权限）"""
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.deleted_at is not None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if not _can_edit_playlist(db, pl, user):
        raise HTTPException(status_code=403, detail="无权操作")

    target = (
        db.query(PlaylistItem)
        .filter(
            PlaylistItem.playlist_id == playlist_id,
            PlaylistItem.track_id == payload.track_id,
        )
        .one_or_none()
    )
    if target is None:
        raise HTTPException(status_code=404, detail="曲目不在该播放列表中")

    items = (
        db.query(PlaylistItem)
        .filter(PlaylistItem.playlist_id == playlist_id)
        .order_by(PlaylistItem.position)
        .all()
    )
    items = [it for it in items if it.id != target.id]
    new_position = max(0, min(payload.new_position, len(items)))
    items.insert(new_position, target)
    # 重新编号
    for idx, it in enumerate(items):
        it.position = idx
    # 播放列表内容变更，手动 touch pl 使其被 bump_version 打戳
    pl.updated_at = datetime.utcnow()
    bump_and_stamp(db, ENTITY_PLAYLISTS, [pl])
    db.commit()
    db.refresh(pl)
    return _playlist_to_out(db, pl)
