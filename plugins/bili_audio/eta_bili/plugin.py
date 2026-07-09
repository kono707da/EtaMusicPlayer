"""bili_audio 插件入口

提供 B站音频区 资源浏览 + 下载到本地节点的能力。
所有路由挂在主应用的 /api/bili 前缀下。
"""
from __future__ import annotations

import logging

from eta_bili.database import init_db
from eta_bili.routers import router

logger = logging.getLogger("etamusic.plugins.bili_audio")

PLUGIN_META = {
    "name": "bili_audio",
    "description": "浏览 B站音频区并下载到本地节点",
    "version": "1.0.0",
    "author": "EtaMusic",
}


def register(app) -> None:
    init_db()
    app.include_router(router)
    logger.info("bili_audio 插件已加载，路由前缀 /api/bili")
