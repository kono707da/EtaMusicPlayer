"""插件加载器

启动流程：
1. 初始化访问端骨架数据库（plugins 表）
2. 扫描 plugins/ 目录，同步到数据库注册表
3. 读取数据库中 enabled=True 的插件，按 name 排序加载
"""
from __future__ import annotations

import importlib
import logging

from app.plugins_manager.database import SessionLocal, init_db as init_access_db
from app.plugins_manager.manager import sync_plugin_registry
from app.plugins_manager.models import Plugin

logger = logging.getLogger("etamusic.plugins")


def _get_enabled_plugins() -> list[str]:
    """从数据库读取已启用的插件名列表"""
    db = SessionLocal()
    try:
        rows = (
            db.query(Plugin)
            .filter(Plugin.enabled.is_(True))
            .order_by(Plugin.name)
            .all()
        )
        return [r.name for r in rows]
    finally:
        db.close()


def load_plugins(app) -> list[str]:
    """加载所有已启用的插件，返回成功加载的插件名列表"""
    # 1. 初始化访问端骨架数据库
    init_access_db()

    # 2. 同步插件注册表（发现新插件/清理失效记录）
    db = SessionLocal()
    try:
        sync_result = sync_plugin_registry(db)
        if sync_result["added"]:
            logger.info("新发现插件: %s", ", ".join(sync_result["added"]))
        if sync_result["removed"]:
            logger.warning("插件文件缺失已禁用: %s", ", ".join(sync_result["removed"]))
    finally:
        db.close()

    # 3. 从数据库读取启用列表并加载
    enabled = _get_enabled_plugins()
    loaded: list[str] = []
    for plugin_name in enabled:
        try:
            module = importlib.import_module(f"app.plugins.{plugin_name}.plugin")
            if not hasattr(module, "register"):
                logger.warning("插件 %s 缺少 register 函数，跳过", plugin_name)
                continue
            module.register(app)
            loaded.append(plugin_name)
            logger.info("插件 %s 已加载", plugin_name)
        except Exception as e:
            logger.error("加载插件 %s 失败: %s", plugin_name, e, exc_info=True)
    return loaded
