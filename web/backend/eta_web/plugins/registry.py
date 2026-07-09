"""插件注册表常量

独立的常量模块，避免 plugins/__init__.py 和 plugins_manager/manager.py 之间的循环导入。
"""
from __future__ import annotations

import logging
from pathlib import Path

from eta_web.config import BASE_DIR, settings

logger = logging.getLogger("eta_web.plugins")

PLUGIN_PACKAGE_MAP: dict[str, str] = {
    "local_node": "eta_node",
    "asmr_one": "eta_asmr",
    "bili_audio": "eta_bili",
}

_DEFAULT_PLUGINS_DIRS = [
    "../../node",
    "../../plugins/asmr_one",
    "../../plugins/bili_audio",
]


def _resolve_plugins_dirs() -> dict[str, Path]:
    """从 config.yaml 的 plugins_dirs 解析插件搜索路径

    plugins_dirs 中的路径相对于 BASE_DIR（web/backend/）解析。
    如果 config.yaml 未配置，使用默认相对路径。
    """
    raw_dirs = settings.plugins_dirs or _DEFAULT_PLUGINS_DIRS
    result: dict[str, Path] = {}
    for raw in raw_dirs:
        p = (BASE_DIR / raw).resolve()
        name = p.name
        if name in PLUGIN_PACKAGE_MAP:
            result[name] = p
        else:
            logger.warning("插件目录 %s 无法映射到已知插件名，跳过", p)
    return result


PLUGIN_SEARCH_PATHS: dict[str, Path] = _resolve_plugins_dirs()
