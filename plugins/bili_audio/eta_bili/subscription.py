"""B站音频订阅检查

定时检查已订阅的 UP 主是否有新音频发布，自动创建下载任务。
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from eta_bili.bili_client import BiliClient
from eta_bili.database import SessionLocal
from eta_bili.models import BiliDownloadTask, BiliSubscription
from eta_bili.downloader import start_download_task

try:
    from eta_node.database import SessionLocal as LocalSession
    from eta_node.models import WatchDir
except ImportError:
    LocalSession = None
    WatchDir = None

logger = logging.getLogger("etamusic.plugins.bili_audio")

_lock = threading.Lock()
_running = False


def _get_first_watch_dir() -> Optional[dict]:
    if LocalSession is None or WatchDir is None:
        return None
    db = LocalSession()
    try:
        wd = db.query(WatchDir).filter(WatchDir.enabled.is_(True)).order_by(WatchDir.id).first()
        if wd:
            return {"id": wd.id, "path": wd.path}
        return None
    finally:
        db.close()


def check_subscription(sub_id: Optional[int] = None) -> int:
    """检查订阅，返回新创建的下载任务数。

    如果 sub_id 指定，只检查该订阅；否则检查所有启用的订阅。
    """
    db = SessionLocal()
    try:
        # 延迟导入避免与 routers.py 的循环导入
        from eta_bili.routers import _get_settings_dict

        settings = _get_settings_dict(db)
        cookie = settings.get("bili_cookie") or ""
        client = BiliClient(cookie=cookie)

        q = db.query(BiliSubscription).filter(BiliSubscription.enabled.is_(True))
        if sub_id is not None:
            q = q.filter(BiliSubscription.id == sub_id)
        subs = q.all()

        if not subs:
            return 0

        default_wd = _get_first_watch_dir()
        default_subdir = settings.get("default_subdir", "BiliAudio")

        new_tasks = 0
        for sub in subs:
            try:
                audios = client.get_user_audios(sub.uid)
            except Exception as e:
                logger.warning("订阅 %s (uid=%s): 获取音频列表失败: %s", sub.id, sub.uid, e)
                continue

            existing_auids = set(
                row[0] for row in db.query(BiliDownloadTask.auid).filter(BiliDownloadTask.auid.isnot(None)).all()
            )

            for audio in audios:
                auid = str(audio.get("id") or audio.get("auid") or "")
                if not auid or auid in existing_auids:
                    continue

                title = audio.get("title") or f"bilibili_audio_{auid}"
                cover_url = audio.get("cover") or ""
                artist = audio.get("author") or audio.get("uname") or ""

                files = []
                play_url = audio.get("play_url") or audio.get("url") or ""
                if play_url:
                    ext = "mp3"
                    if ".flac" in play_url.lower():
                        ext = "flac"
                    elif ".wav" in play_url.lower():
                        ext = "wav"
                    files.append({
                        "path": f"{_sanitize(title)}.{ext}",
                        "url": play_url,
                        "size": audio.get("size") or 0,
                    })

                if not files:
                    continue

                watch_dir_id = default_wd["id"] if default_wd else 0
                if not watch_dir_id:
                    logger.warning("订阅 %s: 无可用 watch_dir，跳过创建下载任务", sub.id)
                    break

                task = BiliDownloadTask(
                    auid=auid,
                    title=title,
                    target_base_url="/local_node",
                    target_watch_dir_id=watch_dir_id,
                    target_subdir=default_subdir,
                    status="pending",
                    files_json=files,
                    selected_paths=[f["path"] for f in files],
                    total_files=len(files),
                    metadata_json={
                        "title": title,
                        "artist": artist,
                        "source_url": f"https://www.bilibili.com/audio/au{auid}",
                        "cover_url": cover_url,
                    },
                )
                db.add(task)
                db.commit()
                db.refresh(task)

                start_download_task(task.id)
                new_tasks += 1
                logger.info("订阅 %s: 创建下载任务 %s (auid=%s, title=%s)", sub.id, task.id, auid, title)

            sub.last_check = datetime.utcnow()
            db.commit()

        return new_tasks
    except Exception as e:
        logger.error("订阅检查异常: %s", e, exc_info=True)
        return 0
    finally:
        db.close()


_INVALID_CHARS = None


def _sanitize(name: str) -> str:
    import re
    if _INVALID_CHARS is None:
        pass
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip().rstrip(".")


def start_subscription_checker(interval_minutes: int = 30) -> None:
    """启动后台订阅检查线程。"""
    global _running

    def _loop():
        global _running
        _running = True
        while _running:
            try:
                n = check_subscription()
                if n > 0:
                    logger.info("订阅检查完成，新建 %d 个下载任务", n)
            except Exception as e:
                logger.error("订阅检查异常: %s", e)
            time.sleep(interval_minutes * 60)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    logger.info("订阅检查线程已启动，间隔 %d 分钟", interval_minutes)


def stop_subscription_checker() -> None:
    global _running
    _running = False
