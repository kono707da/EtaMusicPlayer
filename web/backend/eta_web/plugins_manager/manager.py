"""插件扫描与注册表同步逻辑"""
from __future__ import annotations

import importlib
import json
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
    库类型插件（如 shared）无 plugin.py，返回基础元数据。
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
    """扫描外部插件目录，返回所有可用插件名

    - 普通插件：目录存在且含 {package}/plugin.py
    - 库类型插件（如 shared）：目录存在且含 {package}/__init__.py
    """
    names: list[str] = []
    for name, path in sorted(PLUGIN_SEARCH_PATHS.items()):
        if not path.exists():
            continue
        package_name = PLUGIN_PACKAGE_MAP.get(name, name)
        # 检查是否有 plugin.py（普通插件）或 __init__.py（库类型）
        has_plugin_py = (path / package_name / "plugin.py").exists()
        has_init_py = (path / package_name / "__init__.py").exists()
        if has_plugin_py or has_init_py:
            names.append(name)
    return names


def _parse_dependencies_from_online(name: str) -> tuple[list[dict], bool, bool]:
    """从在线注册表获取插件的依赖信息

    Returns:
        (dependencies, is_library, is_dependency_for_shared)
        - dependencies: 依赖声明列表
        - is_library: 是否为库类型
        - is_dependency: 是否为被依赖的库
    """
    try:
        from eta_web.plugins_manager.online import registry as online_registry

        online = online_registry.get_plugin(name)
        if online:
            return online.dependencies, online.is_library, name == "shared" or online.type == "library"
    except Exception:
        pass
    return [], False, False


def sync_plugin_registry(db: Session) -> dict[str, list[str]]:
    """同步文件系统与数据库注册表

    - 新发现的插件：插入记录（默认 enabled=False，除非 config.plugins_enabled 包含）
    - 已删除的插件文件：保留数据库记录但标记为不可用
    - 已存在的插件：更新 manifest 元数据

    返回 {added: [...], removed: [...], updated: [...]}
    """
    from eta_web.config import settings
    from eta_web.plugins.registry import refresh_plugin_paths

    # 刷新路径，发现新安装或删除的插件
    refresh_plugin_paths()

    discovered = set(discover_plugins())
    existing = {p.name for p in db.query(Plugin).all()}

    added: list[str] = []
    removed: list[str] = []
    updated: list[str] = []

    for name in discovered - existing:
        meta = get_plugin_manifest(name)
        enabled = name in settings.plugins_enabled
        deps, is_library, is_dependency = _parse_dependencies_from_online(name)
        db.add(
            Plugin(
                name=name,
                enabled=enabled,
                description=meta.get("description", ""),
                version=meta.get("version", "1.0.0"),
                author=meta.get("author", ""),
                is_dependency=is_dependency,
                is_library=is_library,
                dependencies=json.dumps(deps, ensure_ascii=False),
            )
        )
        added.append(name)
        logger.info("发现新插件: %s (enabled=%s, library=%s)", name, enabled, is_library)

    for name in discovered & existing:
        meta = get_plugin_manifest(name)
        plugin = db.query(Plugin).filter(Plugin.name == name).one()
        plugin.description = meta.get("description", "")
        plugin.version = meta.get("version", "1.0.0")
        plugin.author = meta.get("author", "")
        # 更新依赖信息
        deps, is_library, is_dependency = _parse_dependencies_from_online(name)
        plugin.is_library = is_library
        plugin.is_dependency = is_dependency
        plugin.dependencies = json.dumps(deps, ensure_ascii=False)
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
    from eta_web.plugins.registry import remove_plugin_path

    path = PLUGIN_SEARCH_PATHS.get(name)
    if not path or not path.exists() or not path.is_dir():
        return False
    shutil.rmtree(path)
    remove_plugin_path(name)
    logger.warning("已删除插件文件: %s", name)
    return True


def update_dependent_by(db: Session, dependency_name: str, dependent_name: str, add: bool = True) -> None:
    """更新插件的 dependent_by 字段

    记录哪个插件依赖了此插件。

    Args:
        dependency_name: 被依赖的插件名（如 shared）
        dependent_name: 依赖者插件名（如 asmr_one）
        add: True=添加依赖关系，False=移除依赖关系
    """
    plugin = db.query(Plugin).filter(Plugin.name == dependency_name).one_or_none()
    if plugin is None:
        return
    try:
        dependents = json.loads(plugin.dependent_by or "[]")
    except (json.JSONDecodeError, TypeError):
        dependents = []

    if add:
        if dependent_name not in dependents:
            dependents.append(dependent_name)
    else:
        if dependent_name in dependents:
            dependents.remove(dependent_name)

    plugin.dependent_by = json.dumps(dependents, ensure_ascii=False)
    plugin.is_dependency = len(dependents) > 0
    db.commit()
