"""bili_audio API 路由

挂在主应用的 /api/bili 前缀下。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from eta_bili.bili_client import BiliClient
from eta_bili.database import SessionLocal
from eta_bili.downloader import cancel_download_task, start_download_task
from eta_bili.models import BiliDownloadTask, BiliSubscription
from eta_bili.subscription import check_subscription

try:
    from eta_node.database import SessionLocal as LocalSession
    from eta_node.models import WatchDir
except ImportError:
    LocalSession = None
    WatchDir = None

router = APIRouter(prefix="/api/bili", tags=["bili"])


def get_db_bili():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DEFAULT_SETTINGS = {
    "bili_cookie": "",
    "default_subdir": "BiliAudio",
    "default_watch_dir_id": "",
    "cache_pool_size_mb": "500",
}


def _get_settings_dict(db: Session) -> dict[str, str]:
    from eta_bili.models import BiliSetting

    rows = db.query(BiliSetting).all()
    out = dict(DEFAULT_SETTINGS)
    for r in rows:
        out[r.key] = r.value
    return out


def _save_settings(db: Session, data: dict[str, Any]) -> dict[str, str]:
    from eta_bili.models import BiliSetting

    out = dict(DEFAULT_SETTINGS)
    for r in db.query(BiliSetting).all():
        out[r.key] = r.value
    for k, v in data.items():
        if k not in DEFAULT_SETTINGS:
            continue
        s = db.query(BiliSetting).filter(BiliSetting.key == k).one_or_none()
        if s is None:
            s = BiliSetting(key=k, value=str(v) if v is not None else "")
            db.add(s)
        else:
            s.value = str(v) if v is not None else ""
        out[k] = str(v) if v is not None else ""
    db.commit()
    return out


def _make_client(db: Session) -> BiliClient:
    settings = _get_settings_dict(db)
    cookie = settings.get("bili_cookie") or ""
    return BiliClient(cookie=cookie)


def _list_local_watch_dirs() -> list[dict]:
    if LocalSession is None or WatchDir is None:
        return []
    db_local = LocalSession()
    try:
        wds = db_local.query(WatchDir).order_by(WatchDir.id).all()
        return [
            {
                "id": wd.id,
                "path": wd.path,
                "recursive": wd.recursive,
                "enabled": wd.enabled,
                "last_scanned_at": wd.last_scanned_at.isoformat() if wd.last_scanned_at else None,
                "created_at": wd.created_at.isoformat() if wd.created_at else None,
            }
            for wd in wds
        ]
    except Exception:
        return []
    finally:
        db_local.close()


# ===== 设置 =====

class SettingsUpdate(BaseModel):
    bili_cookie: Optional[str] = None
    default_subdir: Optional[str] = None
    default_watch_dir_id: Optional[str] = None
    cache_pool_size_mb: Optional[str] = None


@router.get("/settings")
def get_settings(db: Session = Depends(get_db_bili)) -> dict:
    return _get_settings_dict(db)


@router.put("/settings")
def update_settings(
    payload: SettingsUpdate, db: Session = Depends(get_db_bili)
) -> dict:
    data = payload.model_dump(exclude_none=True)
    return _save_settings(db, data)


# ===== 音频浏览 =====

@router.get("/search")
def search(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db_bili),
) -> dict:
    client = _make_client(db)
    try:
        return client.search(keyword, page=page, page_size=page_size)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"B站请求失败: {e}")


@router.get("/audio/{auid}")
def get_audio_detail(auid: str, db: Session = Depends(get_db_bili)) -> dict:
    client = _make_client(db)
    try:
        return client.get_audio_detail(auid)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"B站请求失败: {e}")


@router.get("/user/{uid}/audios")
def get_user_audios(
    uid: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db_bili),
) -> dict:
    client = _make_client(db)
    try:
        return client.get_user_audios(uid, page=page, page_size=page_size)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"B站请求失败: {e}")


@router.get("/cover")
def get_cover(
    url: str = Query(..., min_length=1),
    db: Session = Depends(get_db_bili),
) -> Response:
    client = _make_client(db)
    try:
        r = client.session.get(url, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"封面获取失败: {e}")
    ct = r.headers.get("Content-Type", "image/jpeg")
    return Response(content=r.content, media_type=ct)


# ===== 节点信息 =====

@router.get("/target-nodes")
def list_target_nodes(db: Session = Depends(get_db_bili)) -> dict:
    """列出可下载目标节点

    返回本地节点（需 local_node 已加载）和已配置的远程节点。
    每个节点包含其 watch_dirs 列表，供前端选择下载目标。
    """
    try:
        from eta_web.plugins_manager.routers import _loaded_in_process
    except ImportError:
        _loaded_in_process = set()

    nodes: list[dict] = []
    if "local_node" in _loaded_in_process:
        watch_dirs = _list_local_watch_dirs()
        nodes.append(
            {
                "type": "local_node",
                "id": "local_node",
                "name": "本地节点",
                "base_url": "/local_node",
                "writable": True,
                "watch_dirs": watch_dirs,
                "reason": "",
            }
        )

    # 远程节点
    try:
        from eta_web.plugins_manager.routers import _get_remote_nodes_config
        from eta_web.plugins_manager.database import SessionLocal as WebSession
    except ImportError:
        _get_remote_nodes_config = None

    if _get_remote_nodes_config is not None:
        web_db = WebSession()
        try:
            remote_nodes = _get_remote_nodes_config(web_db)
        finally:
            web_db.close()

        for rn in remote_nodes:
            try:
                from eta_shared.node_client import RemoteNodeClient

                client = RemoteNodeClient(
                    base_url=rn["url"],
                    username=rn.get("username", "admin"),
                    password=rn.get("password", ""),
                    verify_ssl=rn.get("verify_ssl", True),
                )
                watch_dirs = client.get_watch_dirs()
                nodes.append(
                    {
                        "type": "remote",
                        "id": f"remote:{rn['name']}",
                        "name": rn["name"],
                        "base_url": rn["url"],
                        "writable": True,
                        "watch_dirs": watch_dirs,
                        "reason": "",
                    }
                )
            except Exception as e:
                nodes.append(
                    {
                        "type": "remote",
                        "id": f"remote:{rn['name']}",
                        "name": rn["name"],
                        "base_url": rn["url"],
                        "writable": False,
                        "watch_dirs": [],
                        "reason": f"连接失败: {e}",
                    }
                )

    return {"nodes": nodes, "supported_types": ["local_node", "remote"]}


# ===== 下载任务 =====

class DownloadCreate(BaseModel):
    auid: str
    title: str
    source_id: Optional[str] = None
    target_node_id: str = Field(default="local_node")
    watch_dir_id: int
    subdir: Optional[str] = None
    files: list[dict] = Field(default_factory=list)
    selected_paths: Optional[list[str]] = None
    metadata: Optional[dict] = None


@router.post("/downloads", status_code=201)
def create_download(
    payload: DownloadCreate, db: Session = Depends(get_db_bili)
) -> dict:
    settings = _get_settings_dict(db)
    subdir = payload.subdir if payload.subdir is not None else settings.get("default_subdir", "BiliAudio")

    task = BiliDownloadTask(
        auid=payload.auid,
        title=payload.title,
        source_id=payload.source_id,
        target_base_url=payload.target_node_id,
        target_watch_dir_id=payload.watch_dir_id,
        target_subdir=subdir,
        status="pending",
        files_json=payload.files,
        selected_paths=payload.selected_paths or [],
        total_files=len(payload.files),
        metadata_json=payload.metadata or None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    start_download_task(task.id)

    return _task_to_dict(task)


@router.get("/downloads")
def list_downloads(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_bili),
) -> dict:
    q = db.query(BiliDownloadTask)
    if status:
        q = q.filter(BiliDownloadTask.status == status)
    tasks = q.order_by(BiliDownloadTask.id.desc()).limit(limit).all()
    return {
        "tasks": [_task_to_dict(t) for t in tasks],
        "total": len(tasks),
    }


@router.get("/downloads/{task_id}")
def get_download(task_id: int, db: Session = Depends(get_db_bili)) -> dict:
    task = db.get(BiliDownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _task_to_dict(task)


@router.post("/downloads/{task_id}/cancel")
def cancel_download(task_id: int, db: Session = Depends(get_db_bili)) -> dict:
    task = db.get(BiliDownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    ok = cancel_download_task(task_id)
    return {"canceled": ok, "task_id": task_id}


@router.delete("/downloads/{task_id}", status_code=204)
def delete_download(task_id: int, db: Session = Depends(get_db_bili)):
    task = db.get(BiliDownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status in ("pending", "running"):
        raise HTTPException(status_code=400, detail="任务进行中，请先取消")
    db.delete(task)
    db.commit()


# ===== 订阅 =====

class SubscriptionCreate(BaseModel):
    uid: int
    uname: str = ""


class SubscriptionUpdate(BaseModel):
    uname: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("/subscriptions")
def list_subscriptions(db: Session = Depends(get_db_bili)) -> dict:
    subs = db.query(BiliSubscription).order_by(BiliSubscription.id).all()
    return {
        "subscriptions": [
            {
                "id": s.id,
                "uid": s.uid,
                "uname": s.uname,
                "last_check": s.last_check.isoformat() if s.last_check else None,
                "enabled": s.enabled,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ]
    }


@router.post("/subscriptions", status_code=201)
def create_subscription(
    payload: SubscriptionCreate, db: Session = Depends(get_db_bili)
) -> dict:
    existing = (
        db.query(BiliSubscription)
        .filter(BiliSubscription.uid == payload.uid)
        .one_or_none()
    )
    if existing:
        raise HTTPException(status_code=409, detail="该 UP 主已订阅")
    sub = BiliSubscription(
        uid=payload.uid,
        uname=payload.uname or str(payload.uid),
        enabled=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {
        "id": sub.id,
        "uid": sub.uid,
        "uname": sub.uname,
        "enabled": sub.enabled,
    }


@router.put("/subscriptions/{sub_id}")
def update_subscription(
    sub_id: int,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db_bili),
) -> dict:
    sub = db.get(BiliSubscription, sub_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if payload.uname is not None:
        sub.uname = payload.uname
    if payload.enabled is not None:
        sub.enabled = payload.enabled
    db.commit()
    return {
        "id": sub.id,
        "uid": sub.uid,
        "uname": sub.uname,
        "enabled": sub.enabled,
    }


@router.delete("/subscriptions/{sub_id}", status_code=204)
def delete_subscription(sub_id: int, db: Session = Depends(get_db_bili)):
    sub = db.get(BiliSubscription, sub_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="订阅不存在")
    db.delete(sub)
    db.commit()


@router.post("/subscriptions/check")
def trigger_check(
    sub_id: Optional[int] = None,
    db: Session = Depends(get_db_bili),
) -> dict:
    n = check_subscription(sub_id=sub_id)
    return {"checked": True, "new_tasks": n}


# ===== 输出辅助 =====

def _task_to_dict(task: BiliDownloadTask) -> dict:
    return {
        "id": task.id,
        "auid": task.auid,
        "title": task.title,
        "source_id": task.source_id,
        "target_base_url": task.target_base_url,
        "target_watch_dir_id": task.target_watch_dir_id,
        "target_subdir": task.target_subdir,
        "status": task.status,
        "total_files": task.total_files,
        "completed_files": task.completed_files,
        "skipped_files": task.skipped_files,
        "failed_files": task.failed_files,
        "current_file": task.current_file,
        "current_file_size": task.current_file_size,
        "current_file_done": task.current_file_done,
        "error_message": task.error_message,
        "metadata": task.metadata_json,
        "cover_applied": task.cover_applied,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }
