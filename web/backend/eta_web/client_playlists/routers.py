"""客户端播放列表 API 路由

挂在 /api/client-playlists 下。
提供 CRUD + 曲目管理 + 顺序调整。
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from eta_web.plugins_manager.database import get_db
from eta_web.client_playlists.models import ClientPlaylist, ClientPlaylistItem

logger = logging.getLogger("eta_web.client_playlists")

router = APIRouter(prefix="/api/client-playlists", tags=["client-playlists"])

# 系统列表名称
SYSTEM_ALL_MUSIC = "全部音乐"


# ============ Schemas ============


class PlaylistOut(BaseModel):
    id: int
    name: str
    description: str
    is_system: bool
    folder_id: int | None = None
    item_count: int
    created_at: str
    updated_at: str


class PlaylistCreate(BaseModel):
    name: str
    description: str = ""
    folder_id: int | None = None


class PlaylistUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    folder_id: int | None = None


class ItemOut(BaseModel):
    id: int
    track_id: int
    node_id: str
    position: int
    title: str
    artist: str
    album: str
    duration: float


class ItemAdd(BaseModel):
    """添加曲目到播放列表"""
    track_id: int
    node_id: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0


class ItemsAddBatch(BaseModel):
    items: list[ItemAdd]


class ItemsRemoveBatch(BaseModel):
    item_ids: list[int]


class RemoveByTrackRequest(BaseModel):
    """按 (node_id, track_id) 删除客户端播放列表条目（1.2.1）

    用于节点曲目被删除后，访问端清理所有引用该曲目的客户端播放列表项。
    幂等：不存在时返回 removed=0。
    """

    node_id: str
    track_id: int


class ReorderRequest(BaseModel):
    item_id: int
    new_position: int


# ============ Helpers ============


def _playlist_to_out(pl: ClientPlaylist) -> PlaylistOut:
    return PlaylistOut(
        id=pl.id,
        name=pl.name,
        description=pl.description or "",
        is_system=pl.is_system,
        folder_id=pl.folder_id,
        item_count=len(pl.items) if pl.items else 0,
        created_at=pl.created_at.isoformat() if pl.created_at else "",
        updated_at=pl.updated_at.isoformat() if pl.updated_at else "",
    )


def _item_to_out(item: ClientPlaylistItem) -> ItemOut:
    return ItemOut(
        id=item.id,
        track_id=item.track_id,
        node_id=item.node_id,
        position=item.position,
        title=item.title,
        artist=item.artist,
        album=item.album,
        duration=item.duration,
    )


# ============ Routes ============


@router.get("", response_model=list[PlaylistOut])
def list_playlists(db: Session = Depends(get_db)) -> list[PlaylistOut]:
    """列出所有客户端播放列表"""
    rows = db.query(ClientPlaylist).order_by(
        ClientPlaylist.is_system.desc(), ClientPlaylist.created_at
    ).all()
    return [_playlist_to_out(r) for r in rows]


@router.post("", response_model=PlaylistOut, status_code=201)
def create_playlist(payload: PlaylistCreate, db: Session = Depends(get_db)) -> PlaylistOut:
    """创建客户端播放列表"""
    folder_id = payload.folder_id
    if folder_id is not None:
        from eta_web.client_playlists.models import ClientPlaylistFolder
        folder = db.get(ClientPlaylistFolder, folder_id)
        if folder is None:
            raise HTTPException(status_code=404, detail="文件夹不存在")
    pl = ClientPlaylist(name=payload.name, description=payload.description, folder_id=folder_id)
    db.add(pl)
    db.commit()
    db.refresh(pl)
    logger.info("创建客户端播放列表: %s (id=%d)", pl.name, pl.id)
    return _playlist_to_out(pl)


@router.put("/{playlist_id}", response_model=PlaylistOut)
def update_playlist(
    playlist_id: int, payload: PlaylistUpdate, db: Session = Depends(get_db)
) -> PlaylistOut:
    """更新播放列表信息（系统列表名称不可改）"""
    pl = db.get(ClientPlaylist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if pl.is_system and payload.name is not None and payload.name != pl.name:
        raise HTTPException(status_code=400, detail="系统列表名称不可修改")
    if payload.name is not None:
        pl.name = payload.name
    if payload.description is not None:
        pl.description = payload.description
    if payload.folder_id is not None:
        # 0 表示移到根级
        new_folder_id = None if payload.folder_id == 0 else payload.folder_id
        if new_folder_id is not None:
            from eta_web.client_playlists.models import ClientPlaylistFolder
            folder = db.get(ClientPlaylistFolder, new_folder_id)
            if folder is None:
                raise HTTPException(status_code=404, detail="文件夹不存在")
        pl.folder_id = new_folder_id
    db.commit()
    db.refresh(pl)
    return _playlist_to_out(pl)


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)) -> dict:
    """删除播放列表（系统列表不可删）"""
    pl = db.get(ClientPlaylist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    if pl.is_system:
        raise HTTPException(status_code=400, detail="系统列表不可删除")
    db.delete(pl)
    db.commit()
    logger.info("删除客户端播放列表: %s (id=%d)", pl.name, pl.id)
    return {"ok": True}


@router.get("/{playlist_id}/items", response_model=list[ItemOut])
def list_items(playlist_id: int, db: Session = Depends(get_db)) -> list[ItemOut]:
    """获取播放列表曲目（按 position 排序）"""
    pl = db.get(ClientPlaylist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    items = sorted(pl.items, key=lambda x: x.position)
    return [_item_to_out(i) for i in items]


@router.post("/{playlist_id}/items", response_model=list[ItemOut])
def add_items(
    playlist_id: int, payload: ItemsAddBatch, db: Session = Depends(get_db)
) -> list[ItemOut]:
    """批量添加曲目到播放列表末尾

    已存在的（同 track_id + node_id）会跳过。
    """
    pl = db.get(ClientPlaylist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")

    existing = {(i.track_id, i.node_id) for i in pl.items}
    current_max = max((i.position for i in pl.items), default=-1)
    added: list[ClientPlaylistItem] = []
    for it in payload.items:
        if (it.track_id, it.node_id) in existing:
            continue
        current_max += 1
        item = ClientPlaylistItem(
            playlist_id=playlist_id,
            track_id=it.track_id,
            node_id=it.node_id,
            position=current_max,
            title=it.title,
            artist=it.artist,
            album=it.album,
            duration=it.duration,
        )
        db.add(item)
        added.append(item)
    db.commit()
    for a in added:
        db.refresh(a)
    return [_item_to_out(a) for a in added]


@router.delete("/{playlist_id}/items")
def remove_items(
    playlist_id: int, payload: ItemsRemoveBatch, db: Session = Depends(get_db)
) -> dict:
    """批量移除曲目并重排顺序"""
    pl = db.get(ClientPlaylist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    ids_to_remove = set(payload.item_ids)
    remaining = [i for i in pl.items if i.id not in ids_to_remove]
    # 删除
    for i in pl.items:
        if i.id in ids_to_remove:
            db.delete(i)
    # 重排
    for idx, i in enumerate(sorted(remaining, key=lambda x: x.position)):
        i.position = idx
    db.commit()
    return {"ok": True, "removed": len(ids_to_remove)}


@router.delete("/items/by-track")
def remove_items_by_track(
    payload: RemoveByTrackRequest, db: Session = Depends(get_db)
) -> dict:
    """按 (node_id, track_id) 跨所有客户端播放列表删除条目（1.2.1）

    用于节点曲目被软删除/文件删除后，访问端清理全局引用。
    幂等：不存在匹配时返回 removed=0。
    删除后对受影响的每个播放列表按 position 重排，保持顺序连续。
    """
    items = (
        db.query(ClientPlaylistItem)
        .filter(
            ClientPlaylistItem.node_id == payload.node_id,
            ClientPlaylistItem.track_id == payload.track_id,
        )
        .all()
    )
    affected_playlist_ids = {it.playlist_id for it in items}
    for it in items:
        db.delete(it)
    db.flush()
    # 对受影响的播放列表重排 position
    for pl_id in affected_playlist_ids:
        remaining = (
            db.query(ClientPlaylistItem)
            .filter(ClientPlaylistItem.playlist_id == pl_id)
            .order_by(ClientPlaylistItem.position)
            .all()
        )
        for idx, it in enumerate(remaining):
            it.position = idx
    db.commit()
    if items:
        logger.info(
            "按 (node=%s, track=%d) 清理客户端播放列表条目: %d 条, 涉及 %d 个列表",
            payload.node_id, payload.track_id, len(items), len(affected_playlist_ids),
        )
    return {"ok": True, "removed": len(items)}


@router.put("/{playlist_id}/reorder")
def reorder_item(
    playlist_id: int, payload: ReorderRequest, db: Session = Depends(get_db)
) -> dict:
    """调整曲目顺序"""
    pl = db.get(ClientPlaylist, playlist_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="播放列表不存在")
    items = sorted(pl.items, key=lambda x: x.position)
    target = next((i for i in items if i.id == payload.item_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="曲目项不存在")
    old_idx = items.index(target)
    new_idx = max(0, min(payload.new_position, len(items) - 1))
    if old_idx == new_idx:
        return {"ok": True}
    items.pop(old_idx)
    items.insert(new_idx, target)
    for idx, i in enumerate(items):
        i.position = idx
    db.commit()
    return {"ok": True}


def ensure_system_playlists(db: Session) -> None:
    """初始化系统播放列表（"全部音乐"）

    供 main.py 启动时调用。
    """
    existing = db.query(ClientPlaylist).filter(
        ClientPlaylist.is_system.is_(True),
        ClientPlaylist.name == SYSTEM_ALL_MUSIC,
    ).first()
    if existing is None:
        pl = ClientPlaylist(name=SYSTEM_ALL_MUSIC, is_system=True, description="聚合所有节点的全部曲目")
        db.add(pl)
        db.commit()
        logger.info("已创建系统播放列表: %s", SYSTEM_ALL_MUSIC)
