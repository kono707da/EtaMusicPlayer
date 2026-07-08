from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.plugins.bili_audio.bili_client import BiliClient
from app.plugins.bili_audio.database import SessionLocal
from app.plugins.bili_audio.models import BiliDownloadTask, BiliSubscription
from app.plugins.bili_audio.downloader import start_download_task

logger = logging.getLogger("etamusic.plugins.bili_audio")


def check_subscription(sub_id: int) -> dict:
    db = SessionLocal()
    try:
        sub = db.get(BiliSubscription, sub_id)
        if sub is None:
            return {"error": "订阅不存在"}
        if not sub.mid or not sub.season_id:
            return {"error": "订阅缺少 mid 或 season_id"}

        from app.plugins.bili_audio.routers import _get_settings_dict
        settings = _get_settings_dict(db)
        proxy = settings.get("proxy_url") or None
        sessdata = settings.get("sessdata") or None
        client = BiliClient(sessdata=sessdata, proxy_url=proxy)

        all_archives = []
        page_num = 1
        has_more = True
        while has_more:
            try:
                data = client.get_collection_videos(sub.mid, sub.season_id, page_num=page_num)
            except Exception as e:
                sub.status = "error"
                sub.updated_at = datetime.utcnow()
                db.commit()
                return {"error": f"获取合集视频列表失败: {e}"}

            archives = data.get("archives", []) or []
            all_archives.extend(archives)
            page_info = data.get("page", {})
            has_more = page_info.get("has_more", False) if isinstance(page_info, dict) else False
            page_num += 1

        existing_bvids = set()
        all_tasks = db.query(BiliDownloadTask).all()
        for t in all_tasks:
            existing_bvids.add(t.bvid)

        new_count = 0
        new_archives = []
        for arc in all_archives:
            bvid = arc.get("bvid", "")
            if not bvid or bvid in existing_bvids:
                continue
            new_archives.append(arc)

        if sub.auto_download and new_archives:
            for arc in new_archives:
                bvid = arc.get("bvid", "")
                title = arc.get("title", bvid)
                upper = arc.get("author", "")
                mid = arc.get("mid", sub.mid)
                cover = arc.get("pic", "")

                watch_dir_id = sub.target_watch_dir_id
                if not watch_dir_id:
                    try:
                        from app.plugins.local_node.database import SessionLocal as LocalSession
                        from app.plugins.local_node.models import WatchDir
                        db_local = LocalSession()
                        try:
                            wd = db_local.query(WatchDir).filter(WatchDir.enabled.is_(True)).first()
                            if wd:
                                watch_dir_id = wd.id
                        finally:
                            db_local.close()
                    except ImportError:
                        pass

                task = BiliDownloadTask(
                    bvid=bvid,
                    title=title,
                    upper_name=upper or sub.upper_name,
                    upper_mid=mid,
                    cover_url=cover,
                    page_index=0,
                    audio_quality=sub.audio_quality,
                    output_format=sub.output_format,
                    target_watch_dir_id=watch_dir_id,
                    target_subdir=sub.target_subdir or "B站音频",
                    source_url=f"https://www.bilibili.com/video/{bvid}",
                    status="pending",
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                start_download_task(task.id)
                existing_bvids.add(bvid)
                new_count += 1

        sub.video_count = len(all_archives)
        sub.downloaded_count = db.query(BiliDownloadTask).filter(
            BiliDownloadTask.bvid.in_([a.get("bvid") for a in all_archives if a.get("bvid")])
        ).count() if all_archives else 0
        sub.last_checked_at = datetime.utcnow()
        sub.status = "active"
        sub.updated_at = datetime.utcnow()
        db.commit()

        return {
            "total_archives": len(all_archives),
            "new_videos": len(new_archives),
            "new_downloads": new_count,
            "auto_download": sub.auto_download,
            "has_more": False,
        }
    except Exception as e:
        logger.error("检查订阅 %d 异常: %s", sub_id, e, exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


def check_all_subscriptions() -> list[dict]:
    db = SessionLocal()
    try:
        subs = db.query(BiliSubscription).filter(
            BiliSubscription.status.in_(["active", "error"])
        ).all()
        sub_ids = [s.id for s in subs]
    finally:
        db.close()

    results = []
    for sid in sub_ids:
        result = check_subscription(sid)
        results.append({"subscription_id": sid, **result})
    return results
