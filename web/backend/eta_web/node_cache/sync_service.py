"""节点数据同步服务：调用节点增量接口更新访问端缓存

调用时机：前端进入工作台时触发 /api/library/refresh
流程：
1. 对每个在线节点：GET /api/version 获取 data_versions
2. 比对 node_sync_state.last_sync_version
3. 若落后：GET /api/{entity}/changes?since_version=N 拉取增量
4. 更新 node_track_cache / node_playlist_cache + node_sync_state

节点离线时跳过同步，前端读缓存展示（置灰）。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

import requests
from sqlalchemy.orm import Session

from eta_web.plugins_manager.models import RemoteNode
from eta_web.node_cache.models import (
    NodeTrackCache,
    NodePlaylistCache,
    NodeSyncState,
)

logger = logging.getLogger("etamusic.node_cache.sync")

ENTITY_TRACKS = "tracks"
ENTITY_PLAYLISTS = "playlists"


def _get_node_token(node: RemoteNode) -> Optional[str]:
    """登录节点获取 token，失败返回 None（节点离线或认证失败）"""
    try:
        resp = requests.post(
            f"{node.url.rstrip('/')}/api/auth/login",
            json={"username": node.username, "password": node.password},
            verify=node.verify_ssl,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        logger.warning("节点 %s 登录失败: HTTP %s", node.name, resp.status_code)
        return None
    except Exception as e:
        logger.info("节点 %s 不可达，跳过同步: %s", node.name, e)
        return None


def _get_node_version_info(node: RemoteNode, token: str) -> Optional[dict]:
    """GET /api/version，返回包含 data_versions 的完整版本信息"""
    try:
        resp = requests.get(
            f"{node.url.rstrip('/')}/api/version",
            headers={"Authorization": f"Bearer {token}"},
            verify=node.verify_ssl,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        logger.warning("节点 %s 获取版本信息失败: %s", node.name, e)
        return None


def _fetch_changes(node: RemoteNode, token: str, entity: str, since_version: int) -> Optional[dict]:
    """GET /api/{entity}/changes?since_version=N"""
    try:
        resp = requests.get(
            f"{node.url.rstrip('/')}/api/{entity}/changes",
            params={"since_version": since_version},
            headers={"Authorization": f"Bearer {token}"},
            verify=node.verify_ssl,
            timeout=60,  # 增量拉取可能较慢
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("节点 %s 拉取 %s 变更失败: HTTP %s", node.name, entity, resp.status_code)
        return None
    except Exception as e:
        logger.warning("节点 %s 拉取 %s 变更异常: %s", node.name, entity, e)
        return None


def _get_or_create_sync_state(db: Session, node_id: int, entity: str) -> NodeSyncState:
    state = (
        db.query(NodeSyncState)
        .filter(NodeSyncState.node_id == node_id, NodeSyncState.entity_type == entity)
        .one_or_none()
    )
    if state is None:
        state = NodeSyncState(node_id=node_id, entity_type=entity, last_sync_version=0)
        db.add(state)
        db.flush()
    return state


def _apply_track_changes(db: Session, node_id: int, changes: list[dict]) -> None:
    """将曲库变更应用到缓存表

    1.2.1：当曲目被节点软删除时（ch.deleted=true），同步清理所有引用该曲目的
    客户端播放列表条目（ClientPlaylistItem），保持跨层一致性。
    """
    from eta_web.client_playlists.models import ClientPlaylistItem

    # 客户端播放列表项使用的 node_id 字符串格式：remote-{id}
    client_node_id = f"remote-{node_id}"

    # 收集本次被软删除的曲目 id，用于批量清理客户端引用
    deleted_track_ids: list[int] = []

    for ch in changes:
        track_id = ch["id"]
        existing = (
            db.query(NodeTrackCache)
            .filter(NodeTrackCache.node_id == node_id, NodeTrackCache.track_id == track_id)
            .one_or_none()
        )
        if ch.get("deleted"):
            if existing is not None:
                existing.is_deleted = True
            deleted_track_ids.append(track_id)
            continue
        if existing is None:
            existing = NodeTrackCache(node_id=node_id, track_id=track_id)
            db.add(existing)
        existing.title = ch.get("title")
        existing.artist = ch.get("artist")
        existing.album = ch.get("album")
        existing.album_artist = ch.get("album_artist")
        existing.track_no = ch.get("track_no")
        existing.year = ch.get("year")
        existing.genre = ch.get("genre")
        existing.duration = ch.get("duration")
        existing.bitrate = ch.get("bitrate")
        existing.sample_rate = ch.get("sample_rate")
        existing.channels = ch.get("channels")
        existing.file_size = ch.get("file_size")
        existing.cover_embedded = ch.get("cover_embedded", False)
        existing.lyrics_embedded = ch.get("lyrics_embedded", False)
        existing.format_priority = ch.get("format_priority", 1)
        existing.quality_score = ch.get("quality_score", 0)
        existing.is_deleted = False

    # 批量清理客户端播放列表中被软删除曲目的引用（1.2.1）
    if deleted_track_ids:
        removed = (
            db.query(ClientPlaylistItem)
            .filter(
                ClientPlaylistItem.node_id == client_node_id,
                ClientPlaylistItem.track_id.in_(deleted_track_ids),
            )
            .delete(synchronize_session=False)
        )
        if removed > 0:
            logger.info(
                "节点 %s 同步发现 %d 首曲目被软删除，清理 %d 个客户端播放列表引用",
                node_id, len(deleted_track_ids), removed,
            )


def _apply_playlist_changes(db: Session, node_id: int, changes: list[dict]) -> None:
    """将播放列表变更应用到缓存表"""
    for ch in changes:
        playlist_id = ch["id"]
        existing = (
            db.query(NodePlaylistCache)
            .filter(
                NodePlaylistCache.node_id == node_id,
                NodePlaylistCache.playlist_id == playlist_id,
            )
            .one_or_none()
        )
        if ch.get("deleted"):
            if existing is not None:
                existing.is_deleted = True
            continue
        if existing is None:
            existing = NodePlaylistCache(node_id=node_id, playlist_id=playlist_id)
            db.add(existing)
        existing.name = ch.get("name", "")
        existing.owner_id = ch.get("owner_id")
        existing.is_system = ch.get("is_system", False)
        existing.description = ch.get("description")
        existing.items_json = json.dumps(ch.get("items", []), ensure_ascii=False)
        existing.is_deleted = False


def sync_node(db: Session, node: RemoteNode) -> dict:
    """同步单个节点的曲库和播放列表缓存

    Returns: {"node_id": ..., "tracks_synced": N, "playlists_synced": N, "skipped": False/True}
    """
    result = {"node_id": node.id, "tracks_synced": 0, "playlists_synced": 0, "skipped": False}
    token = _get_node_token(node)
    if token is None:
        result["skipped"] = True
        return result

    version_info = _get_node_version_info(node, token)
    if version_info is None:
        result["skipped"] = True
        return result

    data_versions = version_info.get("data_versions", {})
    if not data_versions:
        # 节点版本过低不支持 data_versions，跳过
        result["skipped"] = True
        return result

    # 同步曲库
    current_tracks_ver = data_versions.get(ENTITY_TRACKS, 0)
    tracks_state = _get_or_create_sync_state(db, node.id, ENTITY_TRACKS)
    if current_tracks_ver > tracks_state.last_sync_version:
        changes_data = _fetch_changes(
            node, token, ENTITY_TRACKS, tracks_state.last_sync_version
        )
        if changes_data is not None:
            _apply_track_changes(db, node.id, changes_data.get("changes", []))
            tracks_state.last_sync_version = changes_data.get("current_version", current_tracks_ver)
            tracks_state.last_synced_at = datetime.utcnow()
            result["tracks_synced"] = len(changes_data.get("changes", []))

    # 同步播放列表
    current_playlists_ver = data_versions.get(ENTITY_PLAYLISTS, 0)
    playlists_state = _get_or_create_sync_state(db, node.id, ENTITY_PLAYLISTS)
    if current_playlists_ver > playlists_state.last_sync_version:
        changes_data = _fetch_changes(
            node, token, ENTITY_PLAYLISTS, playlists_state.last_sync_version
        )
        if changes_data is not None:
            _apply_playlist_changes(db, node.id, changes_data.get("changes", []))
            playlists_state.last_sync_version = changes_data.get("current_version", current_playlists_ver)
            playlists_state.last_synced_at = datetime.utcnow()
            result["playlists_synced"] = len(changes_data.get("changes", []))

    db.commit()
    return result


def sync_all_nodes(db: Session) -> list[dict]:
    """同步所有启用的远程节点

    离线节点会被跳过（保留缓存供前端读取）。
    """
    nodes = db.query(RemoteNode).filter(RemoteNode.enabled.is_(True)).all()
    results = []
    for node in nodes:
        try:
            r = sync_node(db, node)
            results.append(r)
        except Exception as e:
            logger.exception("同步节点 %s 失败: %s", node.name, e)
            results.append({
                "node_id": node.id, "skipped": True,
                "error": str(e), "tracks_synced": 0, "playlists_synced": 0
            })
    return results


def cleanup_node_cache(db: Session, node_id: int) -> None:
    """节点删除时清理所有缓存数据 + 客户端播放列表引用

    由 remote-nodes DELETE 端点调用。
    """
    # 1. 清理曲库缓存（CASCADE 会自动清理，但显式删除更安全）
    db.query(NodeTrackCache).filter(NodeTrackCache.node_id == node_id).delete()
    # 2. 清理播放列表缓存
    db.query(NodePlaylistCache).filter(NodePlaylistCache.node_id == node_id).delete()
    # 3. 清理同步状态
    db.query(NodeSyncState).filter(NodeSyncState.node_id == node_id).delete()
    # 4. 清理客户端播放列表中引用该节点的条目
    from eta_web.client_playlists.models import ClientPlaylistItem
    db.query(ClientPlaylistItem).filter(ClientPlaylistItem.node_id == str(node_id)).delete()
    db.commit()
    logger.info("已清理节点 %s 的所有缓存数据", node_id)
