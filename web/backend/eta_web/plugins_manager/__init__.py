"""插件管理模块

访问端自身的能力，独立于任何插件。
负责扫描插件目录、维护插件启用状态、提供管理 API。
"""
from eta_web.plugins_manager.database import engine, SessionLocal, Base, init_db, get_db
from eta_web.plugins_manager.models import Plugin


def __getattr__(name):
    """延迟导入 manager，避免与 plugins 包的循环导入"""
    if name in ("discover_plugins", "sync_plugin_registry", "get_plugin_manifest"):
        from eta_web.plugins_manager import manager
        return getattr(manager, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
