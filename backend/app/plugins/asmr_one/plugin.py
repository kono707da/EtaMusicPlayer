"""asmr_one 插件入口

提供 asmr.one 资源浏览 + 下载到本地节点的能力。
所有路由挂在主应用的 /api/asmr 前缀下。
"""
from __future__ import annotations

import logging

from app.plugins.asmr_one.database import init_db
from app.plugins.asmr_one.routers import router as asmr_router

logger = logging.getLogger("etamusic.plugins.asmr_one")

PLUGIN_META = {
    "name": "asmr_one",
    "description": "浏览 asmr.one 作品并下载到本地节点（带代理支持）",
    "version": "1.0.0",
    "author": "EtaMusic",
}


def register(app) -> None:
    # 初始化插件数据库
    init_db()
    # 注册 API 路由
    app.include_router(asmr_router)
    logger.info("asmr_one 插件已加载，路由前缀 /api/asmr")
