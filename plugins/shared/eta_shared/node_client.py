"""统一节点操作客户端：本地直调 vs 远程 HTTP

下载插件通过此模块与目标节点交互，无需关心节点是本地还是远程。

本地节点（local_node）：同进程直调 eta_node 数据库和函数
远程节点：通过 HTTP API 调用 eta_node standalone 服务
"""
from __future__ import annotations

import logging
import re
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

    def trigger_scan(self, watch_dir_id: Optional[int] = None) -> bool:
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

    def trigger_scan(self, watch_dir_id: Optional[int] = None) -> bool:
        from eta_node.database import SessionLocal
        from eta_node.models import ScanTask
        from eta_node.scanner import run_scan

        db = SessionLocal()
        try:
            task = ScanTask(status="pending", started_at=datetime.utcnow())
            db.add(task)
            db.commit()
            db.refresh(task)
            task_id = task.id
            db.close()
            run_scan(task_id, watch_dir_id=watch_dir_id)
            return True
        except Exception as e:
            logger.warning("触发 local_node 扫描失败: %s", e)
            return False
        finally:
            try:
                db.close()
            except Exception:
                pass

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

    def trigger_scan(self, watch_dir_id: Optional[int] = None) -> bool:
        try:
            payload = {"watch_dir_id": watch_dir_id} if watch_dir_id else {}
            resp = self._request("POST", "/api/scan", json=payload)
            return resp.status_code == 201
        except Exception as e:
            logger.warning("远程触发扫描失败: %s", e)
            return False

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
