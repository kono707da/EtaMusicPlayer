"""网易云插件入口

所有路由挂在主应用的 /api/netease 前缀下。
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from eta_netease.accounts import set_accounts_dir
from eta_netease.routers import router as netease_router

logger = logging.getLogger("etamusic.plugins.netease")

PLUGIN_META = {
    "name": "netease_music",
    "description": "网易云音乐：扫码登录、搜索、播放、推荐、歌单克隆、多账号管理、下载（含ncm解密）",
    "version": "1.1.0",
    "author": "EtaMusic",
    "eta_web_version": ">=1.4.0",
}


def register(app) -> None:
    """注册插件

    1. 设置账号数据目录: web/backend/data/netease_accounts/
    2. 初始化下载任务数据库
    3. 注册路由到主应用
    """
    # 账号数据目录（与 eta_web 数据目录同级）
    data_dir = Path(__file__).resolve().parent.parent.parent.parent / "web" / "backend" / "data" / "netease_accounts"
    data_dir.mkdir(parents=True, exist_ok=True)
    set_accounts_dir(str(data_dir))

    # 初始化下载任务数据库
    try:
        from eta_netease.database import init_db
        init_db()
        logger.info("网易云下载任务数据库已初始化")
    except Exception as e:
        logger.warning("初始化下载任务数据库失败: %s", e)

    app.include_router(netease_router)
    logger.info("网易云插件已加载，路由前缀 /api/netease")
