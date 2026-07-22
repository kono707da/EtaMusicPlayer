"""播放列表文件夹路由：CRUD、递归删除、移动

文件夹是播放列表的树形组织容器：
- parent_id=NULL 表示根级
- 删除文件夹时递归软删除子文件夹和播放列表
- 移动文件夹时防止循环（不能移动到自己的子文件夹）
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import get_current_user_dependency
from eta_node.models import Playlist, PlaylistFolder, User
from eta_node.schemas import PlaylistFolderCreate, PlaylistFolderOut, PlaylistFolderUpdate
from eta_node.versioning import bump_and_stamp, bump_version, ENTITY_PLAYLISTS


router = APIRouter(prefix="/api/playlist-folders", tags=["playlist-folders"])


def _get_folder(db: Session, folder_id: int, user: User) -> PlaylistFolder:
    """获取文件夹并校验权限（所有者或 admin）"""
    folder = db.get(PlaylistFolder, folder_id)
    if folder is None or folder.deleted_at is not None:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    if folder.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="无权操作此文件夹")
    return folder


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
            db.query(PlaylistFolder.id)
            .filter(
                PlaylistFolder.parent_id == current,
                PlaylistFolder.deleted_at.is_(None),
            )
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
            db.query(PlaylistFolder.id)
            .filter(
                PlaylistFolder.parent_id == current,
                PlaylistFolder.deleted_at.is_(None),
            )
            .all()
        )
        for (child_id,) in children:
            result.append(child_id)
            stack.append(child_id)
    return result


@router.get("", response_model=list[PlaylistFolderOut])
def list_folders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """列出当前用户可见的所有文件夹（扁平列表，前端自行构建树）"""
    query = db.query(PlaylistFolder).filter(PlaylistFolder.deleted_at.is_(None))
    if not user.is_admin:
        query = query.filter(PlaylistFolder.owner_id == user.id)
    return query.order_by(PlaylistFolder.name).all()


@router.post("", response_model=PlaylistFolderOut, status_code=201)
def create_folder(
    body: PlaylistFolderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """创建文件夹"""
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="文件夹名不能为空")
    if len(name) > 256:
        raise HTTPException(status_code=400, detail="文件夹名过长")

    parent_id = body.parent_id
    if parent_id is not None:
        parent = db.get(PlaylistFolder, parent_id)
        if parent is None or parent.deleted_at is not None:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        if parent.owner_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="无权在父文件夹下创建")

    folder = PlaylistFolder(
        name=name,
        parent_id=parent_id,
        owner_id=user.id,
    )
    db.add(folder)
    db.flush()
    bump_and_stamp(db, [folder], ENTITY_PLAYLISTS)
    db.commit()
    db.refresh(folder)
    return folder


@router.put("/{folder_id}", response_model=PlaylistFolderOut)
def update_folder(
    folder_id: int,
    body: PlaylistFolderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """重命名或移动文件夹

    移动时检查循环：不能移动到自身或自己的后代下。
    """
    folder = _get_folder(db, folder_id, user)

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="文件夹名不能为空")
        folder.name = name

    if body.parent_id is not None and body.parent_id != folder.parent_id:
        # 移动到新父文件夹
        new_parent_id = body.parent_id
        if new_parent_id == folder.id:
            raise HTTPException(status_code=400, detail="不能将文件夹移动到自身下")
        if _is_descendant(db, folder.id, new_parent_id):
            raise HTTPException(status_code=400, detail="不能将文件夹移动到自己的子文件夹下")
        if new_parent_id != 0:  # 0 表示移动到根
            parent = db.get(PlaylistFolder, new_parent_id)
            if parent is None or parent.deleted_at is not None:
                raise HTTPException(status_code=404, detail="目标父文件夹不存在")
            if parent.owner_id != user.id and not user.is_admin:
                raise HTTPException(status_code=403, detail="无权移动到目标文件夹")
            folder.parent_id = new_parent_id
        else:
            folder.parent_id = None

    bump_and_stamp(db, [folder], ENTITY_PLAYLISTS)
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=204)
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_dependency),
):
    """递归删除文件夹及其所有子文件夹和播放列表

    软删除：设置 deleted_at，保留数据用于增量同步通知。
    """
    folder = _get_folder(db, folder_id, user)

    # 收集所有后代文件夹 id
    all_folder_ids = [folder.id] + _collect_descendants(db, folder.id)
    now = datetime.utcnow()

    # 软删除这些文件夹下的所有播放列表
    playlists = (
        db.query(Playlist)
        .filter(
            Playlist.folder_id.in_(all_folder_ids),
            Playlist.deleted_at.is_(None),
        )
        .all()
    )
    for pl in playlists:
        pl.deleted_at = now
        bump_and_stamp(db, [pl], ENTITY_PLAYLISTS)

    # 软删除所有后代文件夹
    folders = (
        db.query(PlaylistFolder)
        .filter(
            PlaylistFolder.id.in_(all_folder_ids),
            PlaylistFolder.deleted_at.is_(None),
        )
        .all()
    )
    for f in folders:
        f.deleted_at = now
        bump_and_stamp(db, [f], ENTITY_PLAYLISTS)

    db.commit()
