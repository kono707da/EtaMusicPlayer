"""插件加载器

启动流程：
1. 初始化访问端数据库（plugins 表）
2. 从外部目录发现插件，将目录加入 sys.path
3. 同步到数据库注册表
4. 读取数据库中 enabled=True 的插件，按 name 排序加载

插件包映射：
  local_node -> eta_node  (来自 node/ 目录)
  asmr_one   -> eta_asmr  (来自 plugins/asmr_one/ 目录)
  bili_audio -> eta_bili  (来自 plugins/bili_audio/ 目录)
"""
from __future__ import annotations

import importlib
import logging
import sys

from eta_web.plugins.registry import PLUGIN_PACKAGE_MAP, PLUGIN_SEARCH_PATHS
from eta_web.plugins_manager.database import SessionLocal, init_db as init_access_db
from eta_web.plugins_manager.manager import sync_plugin_registry
from eta_web.plugins_manager.models import Plugin

logger = logging.getLogger("eta_web.plugins")


def _ensure_plugin_paths() -> None:
    """将插件目录加入 sys.path（如果尚未加入）"""
    for name, path in PLUGIN_SEARCH_PATHS.items():
        if not path.exists():
            logger.debug("插件目录不存在，跳过: %s (%s)", name, path)
            continue
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            logger.debug("已将 %s 加入 sys.path: %s", name, path_str)


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
    init_access_db()

    _ensure_plugin_paths()

    db = SessionLocal()
    try:
        sync_result = sync_plugin_registry(db)
        if sync_result["added"]:
            logger.info("新发现插件: %s", ", ".join(sync_result["added"]))
        if sync_result["removed"]:
            logger.warning("插件文件缺失已禁用: %s", ", ".join(sync_result["removed"]))
    finally:
        db.close()

    enabled = _get_enabled_plugins()
    loaded: list[str] = []
    for plugin_name in enabled:
        package_name = PLUGIN_PACKAGE_MAP.get(plugin_name)
        if not package_name:
            logger.warning("插件 %s 无包名映射，跳过", plugin_name)
            continue
        try:
            module = importlib.import_module(f"{package_name}.plugin")
            if not hasattr(module, "register"):
                logger.warning("插件 %s (%s) 缺少 register 函数，跳过", plugin_name, package_name)
                continue
            module.register(app)
            loaded.append(plugin_name)
            logger.info("插件 %s (%s) 已加载", plugin_name, package_name)
        except Exception as e:
            logger.error("加载插件 %s (%s) 失败: %s", plugin_name, package_name, e, exc_info=True)
    return loaded
