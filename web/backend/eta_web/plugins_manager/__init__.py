"""插件管理模块

访问端自身的能力，独立于任何插件。
负责扫描插件目录、维护插件启用状态、提供管理 API。
"""
from eta_web.plugins_manager.database import engine, SessionLocal, Base, init_db, get_db
from eta_web.plugins_manager.models import Plugin
from eta_web.plugins_manager.manager import (
    discover_plugins,
    sync_plugin_registry,
    get_plugin_manifest,
)
