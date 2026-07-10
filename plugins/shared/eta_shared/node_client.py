"""统一节点操作客户端：本地直调 vs 远程 HTTP

下载插件通过此模块与目标节点交互，无需关心节点是本地还是远程。

本地节点（local_node）：同进程直调 eta_node 数据库和函数
远程节点：通过 HTTP API 调用 eta_node standalone 服务

节点自治架构：所有写操作通过任务队列串行执行。
- trigger_scan 返回 task_id，通过 get_task_status 轮询
- save_file 可选使用 staging + task 模式
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("etamusic.node_client")

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _build_target_path(
    watch_dir_path: str,
    subdir: Optional[str],
    work_title: str,
    file_rel_path: str,
) -> Path:
    parts = [watch_dir_path]
    if subdir:
        parts.append(subdir.strip("/\\"))
    parts.append(_sanitize(work_title))
    for seg in file_rel_path.split("/"):
        if seg:
            parts.append(_sanitize(seg))
    return Path(*parts)


class NodeClient:
    """节点操作统一接口基类"""

    is_local: bool = False

    def get_watch_dirs(self) -> list[dict]:
        raise NotImplementedError

    def get_watch_dir_path(self, watch_dir_id: int) -> Optional[str]:
        raise NotImplementedError

    def file_exists(
        self,
        watch_dir_id: int,
        subdir: str,
        work_title: str,
        file_rel_path: str,
        expected_size: int,
    ) -> bool:
        raise NotImplementedError

    def save_file(
        self,
        watch_dir_id: int,
        subdir: str,
        work_title: str,
        file_rel_path: str,
        source_path: Path,
    ) -> str:
        """保存文件到节点，返回 saved_to 路径"""
        raise NotImplementedError

    def trigger_scan(self, watch_dir_id: Optional[int] = None) -> Optional[int]:
        """触发扫描，返回 task_id（用于轮询状态），失败返回 None"""
        raise NotImplementedError

    def get_task_status(self, task_id: int) -> Optional[dict]:
        """查询任务状态，返回 {status, progress, result, error_message, ...}"""
        raise NotImplementedError

    def wait_for_task(
        self, task_id: int, timeout: float = 300, poll_interval: float = 2
    ) -> Optional[dict]:
        """等待任务完成，返回最终状态 dict，超时返回 None"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_task_status(task_id)
            if status is None:
                return None
            if status.get("status") in ("completed", "failed", "cancelled"):
                return status
            time.sleep(poll_interval)
        return None

    def record_play_event(self, track_id: int, event_type: str) -> bool:
        """上报播放事件 (play/skip/complete)"""
        raise NotImplementedError

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> Optional[dict]:
        """列出任务（分页），返回 {total, page, size, items}"""
        raise NotImplementedError

    def cancel_task(self, task_id: int) -> bool:
        """取消 pending 任务"""
        raise NotImplementedError

    def stage_file(self, file_path: Path) -> Optional[dict]:
        """暂存文件到节点临时目录，返回 {staging_path, filename, size}"""
        raise NotImplementedError

    def get_audit_logs(
        self,
        action: Optional[str] = None,
        username: Optional[str] = None,
        target_type: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Optional[dict]:
        """查询审计日志（分页），返回 {total, page, size, items}"""
        raise NotImplementedError

    def get_dashboard(self) -> Optional[dict]:
        """获取数据看板"""
        raise NotImplementedError

    def create_playlist(
        self,
        name: str,
        track_paths: list[str],
        description: str = "",
    ) -> Optional[int]:
        raise NotImplementedError

    def add_tracks_to_inbox(self, track_ids: list[int]) -> int:
        raise NotImplementedError

    def find_tracks_by_paths(self, paths: list[str]) -> list[int]:
        raise NotImplementedError


class LocalNodeClient(NodeClient):
    """本地节点：同进程直调"""

    is_local = True

    def get_watch_dirs(self) -> list[dict]:
        from eta_node.database import SessionLocal
        from eta_node.models import WatchDir

        db = SessionLocal()
        try:
            wds = db.query(WatchDir).order_by(WatchDir.id).all()
            return [
                {
                    "id": wd.id,
                    "path": wd.path,
                    "recursive": wd.recursive,
                    "enabled": wd.enabled,
                    "last_scanned_at": wd.last_scanned_at.isoformat()
                    if wd.last_scanned_at
                    else None,
                }
                for wd in wds
            ]
        finally:
            db.close()

    def get_watch_dir_path(self, watch_dir_id: int) -> Optional[str]:
        from eta_node.database import SessionLocal
        from eta_node.models import WatchDir

        db = SessionLocal()
        try:
            wd = db.get(WatchDir, watch_dir_id)
            return wd.path if wd else None
        finally:
            db.close()

    def file_exists(
        self,
        watch_dir_id: int,
        subdir: str,
        work_title: str,
        file_rel_path: str,
        expected_size: int,
    ) -> bool:
        path = self.get_watch_dir_path(watch_dir_id)
        if not path:
            return False
        target = _build_target_path(path, subdir, work_title, file_rel_path)
        return target.exists() and target.stat().st_size == expected_size

    def save_file(
        self,
        watch_dir_id: int,
        subdir: str,
        work_title: str,
        file_rel_path: str,
        source_path: Path,
    ) -> str:
        """本地节点：如果 source_path 已经是目标路径则直接返回，否则复制"""
        path = self.get_watch_dir_path(watch_dir_id)
        if not path:
            raise ValueError(f"watch_dir {watch_dir_id} 不存在")
        target = _build_target_path(path, subdir, work_title, file_rel_path)
        if source_path.resolve() == target.resolve():
            return str(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(source_path, target)
        return str(target)

    def trigger_scan(self, watch_dir_id: Optional[int] = None) -> Optional[int]:
        """提交扫描任务到任务队列，返回 task_id"""
        from eta_node.database import SessionLocal
        from eta_node.models import NodeTask

        db = SessionLocal()
        try:
            task = NodeTask(
                task_type="scan",
                status="pending",
                priority=-10,
                payload={"watch_dir_id": watch_dir_id},
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.info("local_node 扫描任务已提交: #%d (watch_dir_id=%s)", task.id, watch_dir_id)
            return task.id
        except Exception as e:
            logger.warning("触发 local_node 扫描失败: %s", e)
            return None
        finally:
            db.close()

    def get_task_status(self, task_id: int) -> Optional[dict]:
        """查询任务状态"""
        from eta_node.database import SessionLocal
        from eta_node.models import NodeTask

        db = SessionLocal()
        try:
            task = db.get(NodeTask, task_id)
            if task is None:
                return None
            return {
                "id": task.id,
                "task_type": task.task_type,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "error_message": task.error_message,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            }
        finally:
            db.close()

    def record_play_event(self, track_id: int, event_type: str) -> bool:
        """上报播放事件（本地直调）"""
        from eta_node.database import SessionLocal
        from eta_node.models import Track, TrackStats, UserPlayStats
        from datetime import datetime as _dt

        db = SessionLocal()
        try:
            track = db.get(Track, track_id)
            if track is None:
                return False

            now = _dt.utcnow()

            stats = (
                db.query(TrackStats)
                .filter(TrackStats.track_id == track_id)
                .one_or_none()
            )
            if stats is None:
                stats = TrackStats(track_id=track_id, imported_at=track.created_at or now)
                db.add(stats)
                db.flush()

            if event_type == "play":
                stats.total_play_count += 1
                stats.last_played_at = now
            elif event_type == "skip":
                stats.total_skip_count += 1
            elif event_type == "complete":
                stats.total_complete_count += 1

            db.commit()
            return True
        except Exception as e:
            logger.warning("local_node 记录播放事件失败: %s", e)
            db.rollback()
            return False
        finally:
            db.close()

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> Optional[dict]:
        """列出任务（本地直查数据库）"""
        from eta_node.database import SessionLocal
        from eta_node.models import NodeTask

        db = SessionLocal()
        try:
            query = db.query(NodeTask)
            if status is not None:
                query = query.filter(NodeTask.status == status)
            if task_type is not None:
                query = query.filter(NodeTask.task_type == task_type)

            total = query.count()
            items = (
                query.order_by(NodeTask.submitted_at.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            return {
                "total": total,
                "page": page,
                "size": size,
                "items": [
                    {
                        "id": t.id,
                        "task_type": t.task_type,
                        "status": t.status,
                        "priority": t.priority,
                        "payload": t.payload,
                        "result": t.result,
                        "error_message": t.error_message,
                        "progress": t.progress,
                        "submitted_by": t.submitted_by,
                        "submitted_at": t.submitted_at.isoformat() if t.submitted_at else None,
                        "started_at": t.started_at.isoformat() if t.started_at else None,
                        "finished_at": t.finished_at.isoformat() if t.finished_at else None,
                    }
                    for t in items
                ],
            }
        finally:
            db.close()

    def cancel_task(self, task_id: int) -> bool:
        """取消 pending 任务（本地直改数据库）"""
        from datetime import datetime as _dt
        from eta_node.database import SessionLocal
        from eta_node.models import NodeTask

        db = SessionLocal()
        try:
            task = db.get(NodeTask, task_id)
            if task is None or task.status != "pending":
                return False
            task.status = "cancelled"
            task.finished_at = _dt.utcnow()
            db.commit()
            return True
        finally:
            db.close()

    def stage_file(self, file_path: Path) -> Optional[dict]:
        """暂存文件（本地直接复制到 staging 目录）"""
        import shutil
        import uuid
        from eta_node.config import settings

        src = Path(file_path)
        if not src.exists():
            logger.warning("暂存文件不存在: %s", file_path)
            return None

        staging_dir = settings.staging_absolute_path
        staging_dir.mkdir(parents=True, exist_ok=True)
        ext = src.suffix
        staging_name = f"{uuid.uuid4().hex}{ext}"
        staging_path = staging_dir / staging_name
        shutil.copy2(str(src), str(staging_path))

        return {
            "staging_path": str(staging_path),
            "filename": src.name,
            "size": src.stat().st_size,
        }

    def get_audit_logs(
        self,
        action: Optional[str] = None,
        username: Optional[str] = None,
        target_type: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Optional[dict]:
        """查询审计日志（本地直查数据库）"""
        from eta_node.database import SessionLocal
        from eta_node.models import AuditLog

        db = SessionLocal()
        try:
            query = db.query(AuditLog)
            if action is not None:
                query = query.filter(AuditLog.action == action)
            if username is not None:
                query = query.filter(AuditLog.username == username)
            if target_type is not None:
                query = query.filter(AuditLog.target_type == target_type)

            total = query.count()
            items = (
                query.order_by(AuditLog.timestamp.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            return {
                "total": total,
                "page": page,
                "size": size,
                "items": [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                        "user_id": log.user_id,
                        "username": log.username,
                        "client_ip": log.client_ip,
                        "action": log.action,
                        "target_type": log.target_type,
                        "target_id": log.target_id,
                        "detail": log.detail,
                        "task_id": log.task_id,
                    }
                    for log in items
                ],
            }
        finally:
            db.close()

    def get_dashboard(self) -> Optional[dict]:
        """获取数据看板（本地直查数据库）"""
        from datetime import datetime as _dt, timedelta
        from sqlalchemy import func
        from eta_node.database import SessionLocal
        from eta_node.models import (
            PlayHistory, Track, TrackStats, User, UserPlayStats,
        )

        db = SessionLocal()
        try:
            now = _dt.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)

            total_tracks = db.query(func.count(Track.id)).scalar() or 0
            total_play = db.query(func.sum(TrackStats.total_play_count)).scalar() or 0
            total_skip = db.query(func.sum(TrackStats.total_skip_count)).scalar() or 0
            total_complete = db.query(func.sum(TrackStats.total_complete_count)).scalar() or 0
            imported_today = (
                db.query(func.count(TrackStats.track_id))
                .filter(TrackStats.imported_at >= today_start)
                .scalar() or 0
            )
            imported_this_week = (
                db.query(func.count(TrackStats.track_id))
                .filter(TrackStats.imported_at >= week_ago)
                .scalar() or 0
            )

            top_q = (
                db.query(
                    TrackStats.track_id, TrackStats.total_play_count,
                    TrackStats.total_complete_count, Track.title, Track.artist,
                )
                .join(Track, TrackStats.track_id == Track.id)
                .filter(TrackStats.total_play_count > 0)
                .order_by(TrackStats.total_play_count.desc())
                .limit(10)
                .all()
            )
            top_played = [
                {
                    "track_id": r.track_id, "title": r.title, "artist": r.artist,
                    "play_count": r.total_play_count, "complete_count": r.total_complete_count,
                }
                for r in top_q
            ]

            recent_q = (
                db.query(
                    PlayHistory.played_at, PlayHistory.track_id,
                    Track.title, User.username,
                )
                .join(Track, PlayHistory.track_id == Track.id)
                .join(User, PlayHistory.user_id == User.id)
                .order_by(PlayHistory.played_at.desc())
                .limit(10)
                .all()
            )
            recent_plays = [
                {
                    "played_at": r.played_at.isoformat() if r.played_at else None,
                    "track_id": r.track_id, "title": r.title, "username": r.username,
                }
                for r in recent_q
            ]

            active_q = (
                db.query(
                    User.username,
                    func.sum(UserPlayStats.play_count).label("plays"),
                    func.sum(UserPlayStats.complete_count).label("completes"),
                )
                .join(UserPlayStats, UserPlayStats.user_id == User.id)
                .group_by(User.id, User.username)
                .order_by(func.sum(UserPlayStats.play_count).desc())
                .limit(5)
                .all()
            )
            active_users = [
                {
                    "username": r.username,
                    "play_count": int(r.plays) if r.plays else 0,
                    "complete_count": int(r.completes) if r.completes else 0,
                }
                for r in active_q
            ]

            return {
                "total_tracks": total_tracks,
                "total_play_count": total_play,
                "total_skip_count": total_skip,
                "total_complete_count": total_complete,
                "tracks_imported_today": imported_today,
                "tracks_imported_this_week": imported_this_week,
                "top_played_tracks": top_played,
                "recent_plays": recent_plays,
                "active_users": active_users,
            }
        finally:
            db.close()

    def find_tracks_by_paths(self, paths: list[str]) -> list[int]:
        from eta_node.inbox import find_tracks_by_paths as _find

        return _find(paths)

    def add_tracks_to_inbox(self, track_ids: list[int]) -> int:
        from eta_node.inbox import add_tracks_to_inbox as _add

        return _add(track_ids)

    def create_playlist(
        self,
        name: str,
        track_paths: list[str],
        description: str = "",
    ) -> Optional[int]:
        from eta_node.database import SessionLocal
        from eta_node.models import Playlist, PlaylistItem, Track, User

        db = SessionLocal()
        try:
            tracks = (
                db.query(Track).filter(Track.abs_path.in_(track_paths)).all()
            )
            if not tracks:
                logger.warning("未在 local_node 找到对应 Track，跳过播放列表创建")
                return None

            admin = db.query(User).filter(User.is_admin.is_(True)).first()
            if admin is None:
                return None

            pl = (
                db.query(Playlist)
                .filter(
                    Playlist.owner_id == admin.id,
                    Playlist.name == name,
                )
                .one_or_none()
            )
            if pl is None:
                pl = Playlist(
                    name=name,
                    owner_id=admin.id,
                    is_system=False,
                    description=description,
                )
                db.add(pl)
                db.commit()
                db.refresh(pl)

            max_pos = (
                db.query(PlaylistItem.position)
                .filter(PlaylistItem.playlist_id == pl.id)
                .order_by(PlaylistItem.position.desc())
                .first()
            )
            next_pos = (max_pos[0] + 1) if max_pos else 0

            added = 0
            for t in tracks:
                exists = (
                    db.query(PlaylistItem)
                    .filter(
                        PlaylistItem.playlist_id == pl.id,
                        PlaylistItem.track_id == t.id,
                    )
                    .one_or_none()
                )
                if exists:
                    continue
                db.add(
                    PlaylistItem(
                        playlist_id=pl.id,
                        track_id=t.id,
                        position=next_pos,
                    )
                )
                next_pos += 1
                added += 1
            db.commit()
            return pl.id
        except Exception as e:
            logger.warning("创建播放列表失败: %s", e)
            return None
        finally:
            db.close()


class RemoteNodeClient(NodeClient):
    """远程节点：HTTP API 调用

    通过 eta_node standalone 的 HTTP 接口操作远程节点。
    自动登录并缓存 JWT token，401 时自动重新登录。
    """

    is_local = False

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._token: Optional[str] = None
        self._session = requests.Session()

    def _login(self) -> str:
        resp = self._session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": self.username, "password": self.password},
            verify=self.verify_ssl,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise ValueError("登录响应缺少 access_token")
        self._token = token
        return token

    def _ensure_token(self) -> str:
        if self._token:
            return self._token
        return self._login()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """带自动重新登录的 HTTP 请求"""
        last_exc = None
        for attempt in range(2):
            headers = kwargs.pop("headers", {})
            headers["Authorization"] = f"Bearer {self._ensure_token()}"
            try:
                resp = self._session.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=headers,
                    verify=self.verify_ssl,
                    timeout=kwargs.pop("timeout", 600),
                    **kwargs,
                )
                if resp.status_code == 401 and attempt == 0:
                    self._token = None
                    continue
                resp.raise_for_status()
                return resp
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 401 and attempt == 0:
                    self._token = None
                    continue
                last_exc = e
            except requests.RequestException as e:
                last_exc = e
        raise RuntimeError(f"远程节点请求失败: {last_exc}")

    def get_watch_dirs(self) -> list[dict]:
        resp = self._request("GET", "/api/watch-dirs")
        return resp.json()

    def get_watch_dir_path(self, watch_dir_id: int) -> Optional[str]:
        return None

    def file_exists(
        self,
        watch_dir_id: int,
        subdir: str,
        work_title: str,
        file_rel_path: str,
        expected_size: int,
    ) -> bool:
        try:
            resp = self._request(
                "POST",
                "/api/upload/check",
                data={
                    "watch_dir_id": str(watch_dir_id),
                    "subdir": subdir or "",
                    "work_title": work_title,
                    "file_rel_path": file_rel_path,
                    "expected_size": str(expected_size),
                },
            )
            return resp.json().get("exists", False)
        except Exception as e:
            logger.warning("远程检查文件存在性失败: %s", e)
            return False

    def save_file(
        self,
        watch_dir_id: int,
        subdir: str,
        work_title: str,
        file_rel_path: str,
        source_path: Path,
    ) -> str:
        """远程节点：通过 HTTP multipart 上传文件"""
        with open(source_path, "rb") as f:
            files = {"file": (source_path.name, f)}
            data = {
                "watch_dir_id": str(watch_dir_id),
                "subdir": subdir or "",
                "work_title": work_title,
                "file_rel_path": file_rel_path,
            }
            resp = self._request("POST", "/api/upload", files=files, data=data)
        result = resp.json()
        return result.get("saved_to", "")

    def trigger_scan(self, watch_dir_id: Optional[int] = None) -> Optional[int]:
        """提交扫描任务，返回 task_id"""
        try:
            payload = {"watch_dir_id": watch_dir_id}
            resp = self._request("POST", "/api/scan", json=payload)
            data = resp.json()
            task_id = data.get("id")
            logger.info("远程扫描任务已提交: #%s", task_id)
            return task_id
        except Exception as e:
            logger.warning("远程触发扫描失败: %s", e)
            return None

    def get_task_status(self, task_id: int) -> Optional[dict]:
        """查询任务状态"""
        try:
            resp = self._request("GET", f"/api/tasks/{task_id}")
            return resp.json()
        except Exception as e:
            logger.warning("远程查询任务状态失败: %s", e)
            return None

    def record_play_event(self, track_id: int, event_type: str) -> bool:
        """上报播放事件"""
        try:
            resp = self._request(
                "POST",
                "/api/stats/play",
                json={"track_id": track_id, "event_type": event_type},
            )
            return resp.json().get("ok", False)
        except Exception as e:
            logger.warning("远程上报播放事件失败: %s", e)
            return False

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> Optional[dict]:
        """列出任务"""
        try:
            params = {"page": page, "size": size}
            if status is not None:
                params["status"] = status
            if task_type is not None:
                params["task_type"] = task_type
            resp = self._request("GET", "/api/tasks", params=params)
            return resp.json()
        except Exception as e:
            logger.warning("远程查询任务列表失败: %s", e)
            return None

    def cancel_task(self, task_id: int) -> bool:
        """取消 pending 任务"""
        try:
            resp = self._request("POST", f"/api/tasks/{task_id}/cancel")
            return resp.json().get("status") == "cancelled"
        except Exception as e:
            logger.warning("远程取消任务失败: %s", e)
            return False

    def stage_file(self, file_path: Path) -> Optional[dict]:
        """暂存文件到远程节点"""
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f)}
                resp = self._request("POST", "/api/upload/stage", files=files)
            return resp.json()
        except Exception as e:
            logger.warning("远程暂存文件失败: %s", e)
            return None

    def get_audit_logs(
        self,
        action: Optional[str] = None,
        username: Optional[str] = None,
        target_type: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Optional[dict]:
        """查询审计日志"""
        try:
            params = {"page": page, "size": size}
            if action is not None:
                params["action"] = action
            if username is not None:
                params["username"] = username
            if target_type is not None:
                params["target_type"] = target_type
            resp = self._request("GET", "/api/audit/logs", params=params)
            return resp.json()
        except Exception as e:
            logger.warning("远程查询审计日志失败: %s", e)
            return None

    def get_dashboard(self) -> Optional[dict]:
        """获取数据看板"""
        try:
            resp = self._request("GET", "/api/stats/dashboard")
            return resp.json()
        except Exception as e:
            logger.warning("远程获取数据看板失败: %s", e)
            return None

    def find_tracks_by_paths(self, paths: list[str]) -> list[int]:
        try:
            resp = self._request("POST", "/api/inbox/by-paths", json={"paths": paths})
            return resp.json().get("track_ids", [])
        except Exception as e:
            logger.warning("远程按路径查找曲目失败: %s", e)
            return []

    def add_tracks_to_inbox(self, track_ids: list[int]) -> int:
        try:
            resp = self._request("POST", "/api/inbox/add", json={"track_ids": track_ids})
            return resp.json().get("added", 0)
        except Exception as e:
            logger.warning("远程添加收集箱失败: %s", e)
            return 0

    def create_playlist(
        self,
        name: str,
        track_paths: list[str],
        description: str = "",
    ) -> Optional[int]:
        """远程节点暂不支持自动创建播放列表，统一添加到收集箱"""
        return None


def create_node_client(
    node_id: str,
    remote_nodes_config: list[dict] | None = None,
    verify_ssl: bool = True,
) -> Optional[NodeClient]:
    """根据 node_id 创建对应的节点客户端

    node_id == "local_node" → LocalNodeClient（需 local_node 已加载）
    node_id 以 "remote:" 开头 → RemoteNodeClient（从配置中查找 URL/认证信息）
    """
    if node_id == "local_node":
        try:
            return LocalNodeClient()
        except ImportError as e:
            logger.warning("无法创建本地节点客户端: %s", e)
            return None

    if node_id.startswith("remote:"):
        name = node_id[7:]
        if not remote_nodes_config:
            logger.warning("远程节点 %s 未配置", name)
            return None
        for cfg in remote_nodes_config:
            if cfg.get("name") == name:
                return RemoteNodeClient(
                    base_url=cfg["url"],
                    username=cfg.get("username", "admin"),
                    password=cfg.get("password", ""),
                    verify_ssl=cfg.get("verify_ssl", True),
                )
        logger.warning("远程节点 %s 未找到匹配配置", name)
        return None

    logger.warning("未知节点 ID: %s", node_id)
    return None
