"""监控目录管理（admin）"""
from __future__ import annotations

import os
import string
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import require_admin
from app.plugins.local_node.models import Track, User, WatchDir
from app.plugins.local_node.schemas import WatchDirCreate, WatchDirOut, WatchDirUpdate


router = APIRouter(prefix="/api/watch-dirs", tags=["watch-dirs"])


class DirEntry(BaseModel):
    name: str
    path: str


class BrowseResult(BaseModel):
    path: str
    parent: str | None = None
    entries: list[DirEntry] = []



def _to_out(wd: WatchDir) -> WatchDirOut:
    return WatchDirOut(
        id=wd.id,
        path=wd.path,
        recursive=wd.recursive,
        enabled=wd.enabled,
        last_scanned_at=wd.last_scanned_at,
        created_at=wd.created_at,
    )


@router.get("", response_model=list[WatchDirOut])
def list_watch_dirs(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> list[WatchDirOut]:
    """列出所有监控目录"""
    wds = db.query(WatchDir).order_by(WatchDir.id).all()
    return [_to_out(wd) for wd in wds]


@router.get("/browse", response_model=BrowseResult)
def browse_directory(
    path: str | None = Query(default=None, description="要浏览的目录；为空则返回盘符/根"),
    user: User = Depends(require_admin),
) -> BrowseResult:
    """浏览目录结构，仅返回子目录，用于前端路径选择器"""
    # 1. path 为空：Windows 返回盘符列表；其他平台返回根 /
    if not path or not path.strip():
        if os.name == "nt":
            entries = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.isdir(drive) and os.path.exists(drive):
                    entries.append(DirEntry(name=f"{letter}:", path=drive))
            return BrowseResult(path="", parent=None, entries=entries)
        else:
            path = "/"

    target = Path(path).resolve()
    if not target.exists():
        raise HTTPException(status_code=404, detail="路径不存在")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="不是目录")

    entries: list[DirEntry] = []
    try:
        for child in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            # 跳过无权限访问的目录避免后续报错
            try:
                if child.stat() is None:
                    continue
            except (PermissionError, OSError):
                continue
            entries.append(DirEntry(name=child.name, path=str(child)))
    except (PermissionError, OSError) as e:
        raise HTTPException(status_code=403, detail=f"无法访问目录: {e}")

    # 计算父目录（盘符根的父为 None）
    parent: str | None = None
    if os.name == "nt":
        # Windows: 盘符根（如 C:\）的 parent 设为空，让前端回到盘符列表
        if len(str(target)) <= 3 and str(target)[1:3] == ":":
            parent = ""
        else:
            parent = str(target.parent)
    else:
        if str(target) == "/":
            parent = None
        else:
            parent = str(target.parent)

    return BrowseResult(path=str(target), parent=parent, entries=entries)



@router.post("", response_model=WatchDirOut, status_code=201)
def create_watch_dir(
    payload: WatchDirCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> WatchDirOut:
    """新增监控目录"""
    abs_path = str(Path(payload.path).resolve())
    existing = db.query(WatchDir).filter(WatchDir.path == abs_path).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=400, detail="该路径已存在")
    wd = WatchDir(
        path=abs_path,
        recursive=payload.recursive,
        enabled=payload.enabled,
    )
    db.add(wd)
    db.commit()
    db.refresh(wd)
    return _to_out(wd)


@router.put("/{watch_dir_id}", response_model=WatchDirOut)
def update_watch_dir(
    watch_dir_id: int,
    payload: WatchDirUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> WatchDirOut:
    """更新监控目录"""
    wd = db.get(WatchDir, watch_dir_id)
    if wd is None:
        raise HTTPException(status_code=404, detail="监控目录不存在")
    if payload.recursive is not None:
        wd.recursive = payload.recursive
    if payload.enabled is not None:
        wd.enabled = payload.enabled
    db.commit()
    db.refresh(wd)
    return _to_out(wd)


@router.delete("/{watch_dir_id}", status_code=204)
def delete_watch_dir(
    watch_dir_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """删除监控目录，同时删除该目录下的 Track 记录"""
    wd = db.get(WatchDir, watch_dir_id)
    if wd is None:
        raise HTTPException(status_code=404, detail="监控目录不存在")
    # 删除关联 Track（PlaylistItem 通过外键级联删除）
    db.query(Track).filter(Track.watch_dir_id == watch_dir_id).delete(
        synchronize_session=False
    )
    db.delete(wd)
    db.commit()
