"""插件扫描与注册表同步逻辑"""
from __future__ import annotations

import importlib
import logging
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from eta_web.plugins.registry import PLUGIN_PACKAGE_MAP, PLUGIN_SEARCH_PATHS
from eta_web.plugins_manager.models import Plugin

logger = logging.getLogger("eta_web.plugins_manager")


def get_plugin_manifest(name: str) -> dict[str, Any]:
    """读取插件的 manifest 元数据

    约定：插件可在 plugin.py 中导出 PLUGIN_META = {name, description, version, author}
    """
    package_name = PLUGIN_PACKAGE_MAP.get(name)
    if package_name:
        try:
            module = importlib.import_module(f"{package_name}.plugin")
            meta = getattr(module, "PLUGIN_META", None)
            if isinstance(meta, dict):
                return meta
        except Exception:
            pass
    return {
        "name": name,
        "description": "",
        "version": "1.0.0",
        "author": "",
    }


def discover_plugins() -> list[str]:
    """扫描外部插件目录，返回所有可用插件名（目录存在且含 plugin.py）"""
    names: list[str] = []
    for name, path in sorted(PLUGIN_SEARCH_PATHS.items()):
        if not path.exists():
            continue
        package_name = PLUGIN_PACKAGE_MAP.get(name, name)
        if not (path / package_name / "plugin.py").exists():
            continue
        names.append(name)
    return names


def sync_plugin_registry(db: Session) -> dict[str, list[str]]:
    """同步文件系统与数据库注册表

    - 新发现的插件：插入记录（默认 enabled=False，除非 config.plugins_enabled 包含）
    - 已删除的插件文件：保留数据库记录但标记为不可用
    - 已存在的插件：更新 manifest 元数据

    返回 {added: [...], removed: [...], updated: [...]}
    """
    from eta_web.config import settings

    discovered = set(discover_plugins())
    existing = {p.name for p in db.query(Plugin).all()}

    added: list[str] = []
    removed: list[str] = []
    updated: list[str] = []

    for name in discovered - existing:
        meta = get_plugin_manifest(name)
        enabled = name in settings.plugins_enabled
        db.add(
            Plugin(
                name=name,
                enabled=enabled,
                description=meta.get("description", ""),
                version=meta.get("version", "1.0.0"),
                author=meta.get("author", ""),
            )
        )
        added.append(name)
        logger.info("发现新插件: %s (enabled=%s)", name, enabled)

    for name in discovered & existing:
        meta = get_plugin_manifest(name)
        plugin = db.query(Plugin).filter(Plugin.name == name).one()
        plugin.description = meta.get("description", "")
        plugin.version = meta.get("version", "1.0.0")
        plugin.author = meta.get("author", "")
        updated.append(name)

    for name in existing - discovered:
        plugin = db.query(Plugin).filter(Plugin.name == name).one()
        if plugin.enabled:
            plugin.enabled = False
            removed.append(name)
            logger.warning("插件 %s 的文件已缺失，已禁用", name)

    db.commit()
    return {"added": added, "removed": removed, "updated": updated}


def delete_plugin_files(name: str) -> bool:
    """删除插件的整个目录文件"""
    path = PLUGIN_SEARCH_PATHS.get(name)
    if not path or not path.exists() or not path.is_dir():
        return False
    shutil.rmtree(path)
    logger.warning("已删除插件文件: %s", name)
    return True
