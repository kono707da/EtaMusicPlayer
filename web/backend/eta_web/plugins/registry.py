"""插件注册表常量与动态路径解析

独立的常量模块，避免 plugins/__init__.py 和 plugins_manager/manager.py 之间的循环导入。

部署后应用不含任何内置插件，所有插件通过在线安装或手动导入。
插件目录在运行时动态发现：
- ../../node/         (local_node)
- ../../plugins/*/    (其他插件，含 shared)
"""
from __future__ import annotations

import logging
from pathlib import Path

from eta_web.config import BASE_DIR

logger = logging.getLogger("eta_web.plugins")

# 已知插件名 -> Python 包名映射
# 运行时可扩展（手动导入的未知插件会自动检测包名并加入）
PLUGIN_PACKAGE_MAP: dict[str, str] = {
    "local_node": "eta_node",
    "shared": "eta_shared",
    "asmr_one": "eta_asmr",
    "bili_audio": "eta_bili",
    "netease_music": "eta_netease",
}

# 插件搜索路径（name -> 目录 Path）
# 初始为空，由 refresh_plugin_paths() 在启动和安装后填充
# 使用原地变更（clear + update）以便其他模块的引用能看到更新
PLUGIN_SEARCH_PATHS: dict[str, Path] = {}

# 插件根目录
_PLUGINS_ROOT = (BASE_DIR / "../../plugins").resolve()
_NODE_ROOT = (BASE_DIR / "../../node").resolve()


def _detect_package_name(plugin_dir: Path) -> str | None:
    """自动检测插件目录中的 Python 包名

    扫描插件目录下的子目录，找到第一个含 __init__.py 的目录作为包名。
    """
    try:
        for child in sorted(plugin_dir.iterdir()):
            if child.is_dir() and (child / "__init__.py").exists():
                if child.name.isidentifier():
                    return child.name
    except (PermissionError, OSError) as e:
        logger.warning("扫描插件目录 %s 失败: %s", plugin_dir, e)
    return None


def _get_plugin_dir(name: str) -> Path:
    """根据插件名获取预期目录路径"""
    if name == "local_node":
        return _NODE_ROOT
    return _PLUGINS_ROOT / name


def refresh_plugin_paths() -> dict[str, Path]:
    """扫描文件系统，发现已安装的插件并更新 PLUGIN_SEARCH_PATHS

    扫描逻辑：
    1. ../../node/ → local_node（如果存在且含 eta_node/__init__.py）
    2. ../../plugins/*/ → 其他插件（含 shared）

    对于不在 PLUGIN_PACKAGE_MAP 中的目录，自动检测包名。

    Returns:
        更新后的路径字典（与 PLUGIN_SEARCH_PATHS 是同一对象）
    """
    PLUGIN_SEARCH_PATHS.clear()

    # 1. local_node
    if _NODE_ROOT.is_dir():
        if (_NODE_ROOT / "eta_node" / "__init__.py").exists():
            PLUGIN_SEARCH_PATHS["local_node"] = _NODE_ROOT
            PLUGIN_PACKAGE_MAP.setdefault("local_node", "eta_node")
        else:
            logger.debug("node 目录存在但缺少 eta_node 包: %s", _NODE_ROOT)

    # 2. plugins/* 目录
    if _PLUGINS_ROOT.is_dir():
        try:
            for child in sorted(_PLUGINS_ROOT.iterdir()):
                if not child.is_dir():
                    continue
                # 跳过隐藏目录（如 .git）
                if child.name.startswith("."):
                    continue
                plugin_name = child.name
                # 已知映射
                if plugin_name in PLUGIN_PACKAGE_MAP:
                    package_name = PLUGIN_PACKAGE_MAP[plugin_name]
                    # 对于 library 类型（如 shared），不需要 plugin.py
                    if plugin_name == "shared":
                        if (child / package_name / "__init__.py").exists():
                            PLUGIN_SEARCH_PATHS[plugin_name] = child
                    elif (child / package_name / "plugin.py").exists():
                        PLUGIN_SEARCH_PATHS[plugin_name] = child
                    elif (child / package_name / "__init__.py").exists():
                        # 库类型插件只有 __init__.py
                        PLUGIN_SEARCH_PATHS[plugin_name] = child
                    else:
                        logger.debug("插件目录 %s 缺少 %s/plugin.py，跳过", child, package_name)
                else:
                    # 未知插件，自动检测包名
                    detected = _detect_package_name(child)
                    if detected:
                        # 检查是否有 plugin.py（普通插件）或只有 __init__.py（库）
                        has_plugin_py = (child / detected / "plugin.py").exists()
                        if has_plugin_py or True:
                            # 即使没有 plugin.py 也加入路径（可能是库）
                            PLUGIN_SEARCH_PATHS[plugin_name] = child
                            PLUGIN_PACKAGE_MAP[plugin_name] = detected
                            logger.info("发现未知插件: %s (包名: %s)", plugin_name, detected)
        except (PermissionError, OSError) as e:
            logger.warning("扫描 plugins 目录失败: %s", e)

    logger.info(
        "插件路径解析完成: %s",
        ", ".join(f"{n}={p}" for n, p in PLUGIN_SEARCH_PATHS.items()) or "(空)",
    )
    return PLUGIN_SEARCH_PATHS


def add_plugin_path(name: str, plugin_dir: Path, package_name: str | None = None) -> None:
    """安装新插件后调用，注册路径并更新映射

    Args:
        name: 插件名
        plugin_dir: 插件安装目录
        package_name: Python 包名（如已知则传入，None 则自动检测）
    """
    PLUGIN_SEARCH_PATHS[name] = plugin_dir
    if package_name:
        PLUGIN_PACKAGE_MAP[name] = package_name
    elif name not in PLUGIN_PACKAGE_MAP:
        detected = _detect_package_name(plugin_dir)
        if detected:
            PLUGIN_PACKAGE_MAP[name] = detected
    logger.info("已注册插件路径: %s -> %s", name, plugin_dir)


def remove_plugin_path(name: str) -> None:
    """删除插件后调用，移除路径"""
    PLUGIN_SEARCH_PATHS.pop(name, None)
    logger.info("已移除插件路径: %s", name)


# 启动时自动扫描一次
refresh_plugin_paths()
