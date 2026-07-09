"""asmr_one 插件入口

提供 asmr.one 资源浏览 + 下载到本地节点的能力。
所有路由挂在主应用的 /api/asmr 前缀下。
"""
from __future__ import annotations

import logging

from eta_asmr.database import init_db
from eta_asmr.routers import router as asmr_router

logger = logging.getLogger("etamusic.plugins.asmr_one")

PLUGIN_META = {
    "name": "asmr_one",
    "description": "浏览 asmr.one 作品并下载到本地节点（带代理支持）",
    "version": "1.0.0",
    "author": "EtaMusic",
    "eta_web_version": ">=1.0.0,<2.0.0",
}


def register(app) -> None:
    init_db()
    app.include_router(asmr_router)
    logger.info("asmr_one 插件已加载，路由前缀 /api/asmr")
