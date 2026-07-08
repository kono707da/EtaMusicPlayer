"""B站音频插件 API 路由"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.plugins.bili_audio.bili_client import BiliClient
from app.plugins.bili_audio.database import SessionLocal
from app.plugins.bili_audio.downloader import cancel_download_task, start_download_task
from app.plugins.bili_audio.models import BiliDownloadTask, BiliSubscription

logger = logging.getLogger("etamusic.plugins.bili_audio")

router = APIRouter(prefix="/api/bili", tags=["bili_audio"])


def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_settings_dict(db: Session) -> dict:
    from app.plugins.bili_audio.models import BiliSetting

    settings = db.query(BiliSetting).all()
    return {s.key: s.value for s in settings}


def _get_client(db: Session) -> BiliClient:
    settings = _get_settings_dict(db)
    return BiliClient(
        sessdata=settings.get("sessdata"),
        proxy_url=settings.get("proxy_url"),
    )


class SettingUpdate(BaseModel):
    key: str
    value: str


class DownloadCreate(BaseModel):
    url: str
    page_index: int = 0
    audio_quality: int = 30280
    output_format: str = "mp3"
    target_watch_dir_id: Optional[int] = None
    target_subdir: Optional[str] = "B站音频"


class VideoParseRequest(BaseModel):
    url: str


@router.get("/settings")
def get_settings(db: Session = Depends(_get_db)):
    from app.plugins.bili_audio.models import BiliSetting

    settings = db.query(BiliSetting).all()
    result = {}
    for s in settings:
        if s.key == "sessdata" and s.value:
            result[s.key] = s.value[:8] + "..." if len(s.value) > 8 else s.value
        else:
            result[s.key] = s.value
    return result


@router.put("/settings")
def update_settings(updates: list[SettingUpdate], db: Session = Depends(_get_db)):
    from app.plugins.bili_audio.models import BiliSetting

    for u in updates:
        s = db.query(BiliSetting).filter(BiliSetting.key == u.key).one_or_none()
        if s is None:
            s = BiliSetting(key=u.key, value=u.value)
            db.add(s)
        else:
            s.value = u.value
    db.commit()
    return {"ok": True}


@router.post("/parse")
def parse_video(req: VideoParseRequest, db: Session = Depends(_get_db)):
    client = _get_client(db)
    bvid = client.parse_bvid(req.url)
    if not bvid:
        raise HTTPException(status_code=400, detail="无法解析BV号，请输入正确的B站视频链接")
    try:
        info = client.get_video_info(bvid)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取视频信息失败: {e}")

    pages = info.get("pages", [])
    return {
        "bvid": bvid,
        "title": info.get("title", ""),
        "upper_name": info.get("owner", {}).get("name", ""),
        "upper_mid": info.get("owner", {}).get("mid"),
        "cover_url": info.get("pic", ""),
        "duration": info.get("duration", 0),
        "desc": info.get("desc", ""),
        "pages": [
            {
                "page": p.get("page", 1),
                "cid": p.get("cid"),
                "part": p.get("part", ""),
                "duration": p.get("duration", 0),
            }
            for p in pages
        ],
        "source_url": f"https://www.bilibili.com/video/{bvid}",
    }


@router.get("/target-nodes")
def list_target_nodes(db: Session = Depends(_get_db)):
    try:
        from app.plugins.local_node.database import SessionLocal as LocalSession
        from app.plugins.local_node.models import WatchDir

        db_local = LocalSession()
        try:
            dirs = db_local.query(WatchDir).filter(WatchDir.enabled.is_(True)).all()
            return [
                {"id": d.id, "path": d.path}
                for d in dirs
            ]
        finally:
            db_local.close()
    except ImportError:
        return []


@router.post("/downloads")
def create_download(req: DownloadCreate, db: Session = Depends(_get_db)):
    client = _get_client(db)
    bvid = client.parse_bvid(req.url)
    if not bvid:
        raise HTTPException(status_code=400, detail="无法解析BV号")

    try:
        info = client.get_video_info(bvid)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取视频信息失败: {e}")

    if not req.target_watch_dir_id:
        try:
            from app.plugins.local_node.database import SessionLocal as LocalSession
            from app.plugins.local_node.models import WatchDir

            db_local = LocalSession()
            try:
                wd = db_local.query(WatchDir).filter(WatchDir.enabled.is_(True)).first()
                if wd:
                    req.target_watch_dir_id = wd.id
            finally:
                db_local.close()
        except ImportError:
            pass

    task = BiliDownloadTask(
        bvid=bvid,
        title=info.get("title", bvid),
        upper_name=info.get("owner", {}).get("name"),
        upper_mid=info.get("owner", {}).get("mid"),
        cover_url=info.get("pic"),
        page_index=req.page_index,
        page_title=info.get("pages", [{}])[req.page_index].get("part") if info.get("pages") else None,
        audio_quality=req.audio_quality,
        output_format=req.output_format,
        target_watch_dir_id=req.target_watch_dir_id,
        target_subdir=req.target_subdir,
        source_url=f"https://www.bilibili.com/video/{bvid}",
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    start_download_task(task.id)
    return {"id": task.id, "status": task.status}


@router.get("/downloads")
def list_downloads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(_get_db),
):
    total = db.query(BiliDownloadTask).count()
    tasks = (
        db.query(BiliDownloadTask)
        .order_by(BiliDownloadTask.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": t.id,
                "bvid": t.bvid,
                "title": t.title,
                "upper_name": t.upper_name,
                "cover_url": t.cover_url,
                "page_index": t.page_index,
                "page_title": t.page_title,
                "audio_quality": t.audio_quality,
                "output_format": t.output_format,
                "status": t.status,
                "progress": t.progress,
                "saved_to": t.saved_to,
                "file_size": t.file_size,
                "error_message": t.error_message,
                "source_url": t.source_url,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "finished_at": t.finished_at.isoformat() if t.finished_at else None,
            }
            for t in tasks
        ],
    }


@router.get("/downloads/{task_id}")
def get_download(task_id: int, db: Session = Depends(_get_db)):
    task = db.get(BiliDownloadTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "id": task.id,
        "bvid": task.bvid,
        "title": task.title,
        "upper_name": task.upper_name,
        "cover_url": task.cover_url,
        "page_index": task.page_index,
        "page_title": task.page_title,
        "audio_quality": task.audio_quality,
        "output_format": task.output_format,
        "status": task.status,
        "progress": task.progress,
        "saved_to": task.saved_to,
        "file_size": task.file_size,
        "error_message": task.error_message,
        "source_url": task.source_url,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }


@router.post("/downloads/{task_id}/cancel")
def cancel_download(task_id: int, db: Session = Depends(_get_db)):
    ok = cancel_download_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="无法取消（任务不存在或已完成）")
    return {"ok": True}


@router.delete("/downloads/{task_id}")
def delete_download(task_id: int, db: Session = Depends(_get_db)):
    task = db.get(BiliDownloadTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status in ("pending", "running"):
        cancel_download_task(task_id)
    db.delete(task)
    db.commit()
    return {"ok": True}


class SubscriptionCreate(BaseModel):
    url: str
    auto_download: bool = True
    audio_quality: int = 30280
    output_format: str = "mp3"
    target_watch_dir_id: Optional[int] = None
    target_subdir: Optional[str] = "B站音频"


@router.post("/subscriptions")
def create_subscription(req: SubscriptionCreate, db: Session = Depends(_get_db)):
    client = _get_client(db)
    parsed = client.parse_collection_url(req.url)
    if not parsed:
        raise HTTPException(status_code=400, detail="无法解析合集链接，请输入正确的B站合集/列表链接")

    mid, season_id = parsed
    try:
        data = client.get_collection_videos(mid, season_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取合集信息失败: {e}")

    meta = data.get("meta", {}) or {}
    archives = data.get("archives", []) or []

    upper_name = meta.get("upper_name", "")
    if not upper_name:
        try:
            upper_info = client.get_upper_info(mid)
            if upper_info:
                upper_name = upper_info.get("name", "")
        except Exception:
            pass

    sub = BiliSubscription(
        url=req.url,
        sub_type="collection",
        title=meta.get("name", meta.get("title", "")),
        upper_name=upper_name,
        upper_mid=mid,
        season_id=season_id,
        mid=mid,
        video_count=len(archives),
        downloaded_count=0,
        auto_download=req.auto_download,
        audio_quality=req.audio_quality,
        output_format=req.output_format,
        target_watch_dir_id=req.target_watch_dir_id,
        target_subdir=req.target_subdir,
        status="active",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    if req.auto_download:
        from app.plugins.bili_audio.subscription import check_subscription
        check_subscription(sub.id)
        db.refresh(sub)

    return {
        "id": sub.id,
        "url": sub.url,
        "title": sub.title,
        "upper_name": sub.upper_name,
        "video_count": sub.video_count,
        "downloaded_count": sub.downloaded_count,
        "auto_download": sub.auto_download,
        "status": sub.status,
        "last_checked_at": sub.last_checked_at.isoformat() if sub.last_checked_at else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }


@router.get("/subscriptions")
def list_subscriptions(db: Session = Depends(_get_db)):
    subs = db.query(BiliSubscription).order_by(BiliSubscription.id.desc()).all()
    return {
        "items": [
            {
                "id": s.id,
                "url": s.url,
                "sub_type": s.sub_type,
                "title": s.title,
                "upper_name": s.upper_name,
                "upper_mid": s.upper_mid,
                "season_id": s.season_id,
                "mid": s.mid,
                "video_count": s.video_count,
                "downloaded_count": s.downloaded_count,
                "auto_download": s.auto_download,
                "audio_quality": s.audio_quality,
                "output_format": s.output_format,
                "target_watch_dir_id": s.target_watch_dir_id,
                "target_subdir": s.target_subdir,
                "last_checked_at": s.last_checked_at.isoformat() if s.last_checked_at else None,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in subs
        ]
    }


@router.get("/subscriptions/{sub_id}")
def get_subscription(sub_id: int, db: Session = Depends(_get_db)):
    sub = db.get(BiliSubscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return {
        "id": sub.id,
        "url": sub.url,
        "sub_type": sub.sub_type,
        "title": sub.title,
        "upper_name": sub.upper_name,
        "upper_mid": sub.upper_mid,
        "season_id": sub.season_id,
        "mid": sub.mid,
        "video_count": sub.video_count,
        "downloaded_count": sub.downloaded_count,
        "auto_download": sub.auto_download,
        "audio_quality": sub.audio_quality,
        "output_format": sub.output_format,
        "target_watch_dir_id": sub.target_watch_dir_id,
        "target_subdir": sub.target_subdir,
        "last_checked_at": sub.last_checked_at.isoformat() if sub.last_checked_at else None,
        "status": sub.status,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
        "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
    }


@router.post("/subscriptions/{sub_id}/check")
def check_sub(sub_id: int, db: Session = Depends(_get_db)):
    from app.plugins.bili_audio.subscription import check_subscription
    result = check_subscription(sub_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.delete("/subscriptions/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(_get_db)):
    sub = db.get(BiliSubscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    db.delete(sub)
    db.commit()
    return {"ok": True}


@router.put("/subscriptions/{sub_id}")
def update_subscription(sub_id: int, req: dict, db: Session = Depends(_get_db)):
    sub = db.get(BiliSubscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    for key in ("auto_download", "audio_quality", "output_format", "target_watch_dir_id", "target_subdir", "status"):
        if key in req:
            setattr(sub, key, req[key])
    sub.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sub)
    return {"ok": True}
