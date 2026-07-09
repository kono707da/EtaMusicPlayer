"""local_node 插件入口

将完整的节点功能（扫描/流式/播放列表/用户/权限/元数据/去重/音质）
封装为 FastAPI 子应用，挂载到主应用的 /local_node 路径下。

挂载后，访问端可通过 http://<host>:<port>/local_node/api/... 访问本地节点，
与访问远程节点（http://<remote>:8000/api/...）在协议层面完全等价。
"""
from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eta_node.config import settings
from eta_node.security import hash_password

from eta_node.database import SessionLocal, init_db
from eta_node.models import DedupConfig, Playlist, User, SYSTEM_PLAYLIST_ALL, SYSTEM_PLAYLIST_INBOX
from eta_node.dedup import DEFAULT_FIELDS, DEFAULT_DURATION_TOLERANCE

from eta_node.routers import (
    auth,
    dedup,
    inbox,
    metadata,
    permissions,
    playlists,
    quality,
    scan,
    tracks,
    upload,
    users,
    watch_dirs,
)

logger = logging.getLogger("etamusic.plugins.local_node")

# 插件元数据（供 plugins_manager 读取展示）
PLUGIN_META = {
    "name": "local_node",
    "description": "本地节点：完整的音乐库服务（扫描/流式/播放列表/用户/权限/元数据/去重/音质）",
    "version": "1.0.0",
    "author": "EtaMusic",
    "eta_web_version": ">=1.0.0,<2.0.0",
}


def bootstrap() -> None:
    """节点启动初始化：建表、创建 admin 用户、系统播放列表、默认去重配置"""
    init_db()
    db = SessionLocal()
    try:
        # 1. 创建默认 admin 用户
        admin = db.query(User).filter(User.username == "admin").one_or_none()
        if admin is None:
            admin = User(
                username="admin",
                password_hash=hash_password(settings.default_admin_password),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            logger.warning(
                "本地节点：已创建默认管理员 admin / %s，请尽快修改密码！",
                settings.default_admin_password,
            )
        else:
            logger.info("本地节点：管理员账户 admin 已存在")

        # 2. 创建 "全部音乐" 系统播放列表
        sys_pl = (
            db.query(Playlist)
            .filter(Playlist.is_system.is_(True), Playlist.name == SYSTEM_PLAYLIST_ALL)
            .one_or_none()
        )
        if sys_pl is None:
            sys_pl = Playlist(
                name=SYSTEM_PLAYLIST_ALL,
                owner_id=admin.id,
                is_system=True,
                description="系统自动维护：所有已扫描曲目",
            )
            db.add(sys_pl)
            db.commit()
            logger.info("本地节点：已创建系统播放列表 '%s'", SYSTEM_PLAYLIST_ALL)

        inbox_pl = (
            db.query(Playlist)
            .filter(Playlist.is_system.is_(True), Playlist.name == SYSTEM_PLAYLIST_INBOX)
            .one_or_none()
        )
        if inbox_pl is None:
            inbox_pl = Playlist(
                name=SYSTEM_PLAYLIST_INBOX,
                owner_id=admin.id,
                is_system=True,
                description="系统自动维护：所有下载的音频",
            )
            db.add(inbox_pl)
            db.commit()
            logger.info("本地节点：已创建系统播放列表 '%s'", SYSTEM_PLAYLIST_INBOX)

        # 3. 创建默认 DedupConfig（id=1）
        cfg = db.get(DedupConfig, 1)
        if cfg is None:
            cfg = DedupConfig(
                id=1,
                fields=json.dumps(DEFAULT_FIELDS),
                duration_tolerance=DEFAULT_DURATION_TOLERANCE,
                enabled=True,
            )
            db.add(cfg)
            db.commit()
            logger.info("本地节点：已创建默认去重配置")
    finally:
        db.close()


def create_local_node_app() -> FastAPI:
    """创建本地节点 FastAPI 子应用"""
    sub_app = FastAPI(
        title="EtaMusic 本地节点",
        description="local_node 插件提供的完整节点服务",
        version="1.0.0",
    )

    # CORS（子应用需独立配置）
    sub_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
    )

    # 注册全部节点路由
    sub_app.include_router(auth.router)
    sub_app.include_router(tracks.router)
    sub_app.include_router(playlists.router)
    sub_app.include_router(watch_dirs.router)
    sub_app.include_router(scan.router)
    sub_app.include_router(upload.router)
    sub_app.include_router(inbox.router)
    sub_app.include_router(users.router)
    sub_app.include_router(permissions.router)
    sub_app.include_router(dedup.router)
    sub_app.include_router(quality.router)
    sub_app.include_router(metadata.router)

    @sub_app.get("/health", tags=["root"])
    def local_health() -> dict:
        """本地节点健康检查"""
        return {"status": "ok", "node": "local_node"}

    return sub_app


def register(app) -> None:
    """插件注册入口：初始化节点并挂载子应用"""
    # 1. 启动初始化（建表、admin、系统播放列表）
    bootstrap()

    # 2. 创建并挂载子应用
    local_app = create_local_node_app()
    app.mount("/local_node", local_app)

    logger.info("本地节点已挂载到 /local_node")
