"""客户端播放列表文件夹 API 路由

挂在 /api/client-playlist-folders 下。
提供 CRUD + 递归删除 + 移动（防循环）。

客户端文件夹是全局的（不属于任何节点或用户）。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from eta_web.plugins_manager.database import get_db
from eta_web.client_playlists.models import ClientPlaylist, ClientPlaylistFolder

logger = logging.getLogger("eta_web.client_playlists.folders")

router = APIRouter(prefix="/api/client-playlist-folders", tags=["client-playlist-folders"])


# ============ Schemas ============


class FolderOut(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    created_at: str
    updated_at: str


class FolderCreate(BaseModel):
    name: str
    parent_id: int | None = None


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


# ============ Helpers ============


def _folder_to_out(f: ClientPlaylistFolder) -> FolderOut:
    return FolderOut(
        id=f.id,
        name=f.name,
        parent_id=f.parent_id,
        created_at=f.created_at.isoformat() if f.created_at else "",
        updated_at=f.updated_at.isoformat() if f.updated_at else "",
    )


def _is_descendant(db: Session, folder_id: int, candidate_parent_id: int) -> bool:
    """检查 candidate_parent_id 是否是 folder_id 的后代（防止循环移动）"""
    if folder_id == candidate_parent_id:
        return True
    stack = [candidate_parent_id]
    visited: set[int] = set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        children = (
            db.query(ClientPlaylistFolder.id)
            .filter(ClientPlaylistFolder.parent_id == current)
            .all()
        )
        for (child_id,) in children:
            if child_id == folder_id:
                return True
            stack.append(child_id)
    return False


def _collect_descendants(db: Session, folder_id: int) -> list[int]:
    """收集 folder_id 及其所有后代文件夹 id（不含自身）"""
    result: list[int] = []
    stack = [folder_id]
    visited: set[int] = set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        children = (
            db.query(ClientPlaylistFolder.id)
            .filter(ClientPlaylistFolder.parent_id == current)
            .all()
        )
        for (child_id,) in children:
            result.append(child_id)
            stack.append(child_id)
    return result


# ============ Routes ============


@router.get("", response_model=list[FolderOut])
def list_folders(db: Session = Depends(get_db)) -> list[FolderOut]:
    """列出所有客户端文件夹（扁平列表，前端自行构建树）"""
    rows = db.query(ClientPlaylistFolder).order_by(ClientPlaylistFolder.name).all()
    return [_folder_to_out(r) for r in rows]


@router.post("", response_model=FolderOut, status_code=201)
def create_folder(payload: FolderCreate, db: Session = Depends(get_db)) -> FolderOut:
    """创建文件夹"""
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="文件夹名不能为空")
    if len(name) > 256:
        raise HTTPException(status_code=400, detail="文件夹名过长")

    parent_id = payload.parent_id
    if parent_id is not None:
        parent = db.get(ClientPlaylistFolder, parent_id)
        if parent is None:
            raise HTTPException(status_code=404, detail="父文件夹不存在")

    folder = ClientPlaylistFolder(name=name, parent_id=parent_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    logger.info("创建客户端文件夹: %s (id=%d)", folder.name, folder.id)
    return _folder_to_out(folder)


@router.put("/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: int, payload: FolderUpdate, db: Session = Depends(get_db)
) -> FolderOut:
    """重命名或移动文件夹

    移动时检查循环：不能移动到自身或自己的后代下。
    """
    folder = db.get(ClientPlaylistFolder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="文件夹名不能为空")
        folder.name = name

    if payload.parent_id is not None and payload.parent_id != folder.parent_id:
        new_parent_id = payload.parent_id
        if new_parent_id == folder.id:
            raise HTTPException(status_code=400, detail="不能将文件夹移动到自身下")
        if _is_descendant(db, folder.id, new_parent_id):
            raise HTTPException(status_code=400, detail="不能将文件夹移动到自己的子文件夹下")
        if new_parent_id != 0:  # 0 表示移动到根
            parent = db.get(ClientPlaylistFolder, new_parent_id)
            if parent is None:
                raise HTTPException(status_code=404, detail="目标父文件夹不存在")
            folder.parent_id = new_parent_id
        else:
            folder.parent_id = None

    db.commit()
    db.refresh(folder)
    return _folder_to_out(folder)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, db: Session = Depends(get_db)) -> dict:
    """递归删除文件夹及其所有子文件夹和播放列表"""
    folder = db.get(ClientPlaylistFolder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    # 收集所有后代文件夹 id
    all_folder_ids = [folder.id] + _collect_descendants(db, folder.id)

    # 删除这些文件夹下的所有播放列表（系统列表的 folder_id 置空）
    playlists = (
        db.query(ClientPlaylist)
        .filter(ClientPlaylist.folder_id.in_(all_folder_ids))
        .all()
    )
    for pl in playlists:
        if pl.is_system:
            pl.folder_id = None
        else:
            db.delete(pl)

    # 删除所有后代文件夹（CASCADE 会自动处理）
    folders = (
        db.query(ClientPlaylistFolder)
        .filter(ClientPlaylistFolder.id.in_(all_folder_ids))
        .all()
    )
    for f in folders:
        db.delete(f)

    db.commit()
    logger.info("递归删除客户端文件夹: id=%d (含 %d 个子文件夹, %d 个播放列表)",
                folder_id, len(all_folder_ids) - 1, len([p for p in playlists if not p.is_system]))
    return {"deleted": True, "folder_id": folder_id}
