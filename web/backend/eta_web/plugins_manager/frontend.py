"""插件前端资源管理

每个外部插件（local_node 除外）可在 plugins/<name>/frontend/ 目录下提供独立的前端 bundle：
- manifest.json: 插件元数据（name/version/entry/routes/navItems/nodeFormPresets）
- dist/: 构建产物（index.[hash].js + 资源文件），由插件开发者本地构建后提交

主应用通过 /api/plugins/<name>/frontend-manifest 读取 manifest，
通过 /plugins-assets/<name>/ 静态挂载 dist 目录。

插件前端代码运行时通过 window.__etamusic 取用主应用暴露的依赖（vue/pinia/ui 等），
不打包这些依赖，构建产物仅包含插件自身的视图和逻辑。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from eta_web.plugins.registry import PLUGIN_SEARCH_PATHS

logger = logging.getLogger("eta_web.plugins.frontend")


def get_plugin_frontend_dir(name: str) -> Path:
    """获取插件的 frontend 目录路径

    返回 plugins/<name>/frontend/，不存在则返回不存在的 Path（调用方负责判断）。
    """
    plugin_dir = PLUGIN_SEARCH_PATHS.get(name)
    if not plugin_dir:
        return Path()  # 占位，调用方应先检查插件是否存在
    return plugin_dir / "frontend"


def get_plugin_frontend_dist(name: str) -> Path:
    """获取插件前端构建产物目录"""
    return get_plugin_frontend_dir(name) / "dist"


def read_frontend_manifest(name: str) -> dict[str, Any] | None:
    """读取插件前端 manifest

    优先读 dist/manifest.json（构建后的，含正确的 entry 路径）。
    若 dist 不存在则读 frontend/manifest.json（开发用，entry 可能是相对路径）。

    Returns:
        manifest dict 或 None（插件无前端或 manifest 缺失）
    """
    dist_dir = get_plugin_frontend_dist(name)
    dist_manifest = dist_dir / "manifest.json"
    if dist_manifest.is_file():
        try:
            with dist_manifest.open("r", encoding="utf-8") as f:
                m = json.load(f)
            # 构建后的 entry 是相对 dist 的路径，前端访问时需加上 /plugins-assets/<name>/ 前缀
            entry = m.get("entry")
            if entry and not entry.startswith(("http://", "https://", "/")):
                m["entry"] = f"/plugins-assets/{name}/{entry.lstrip('/')}"
            return m
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("读取插件 %s 的 dist/manifest.json 失败: %s", name, e)
            return None

    # dist 不存在，读源码 manifest（仅用于开发调试，不保证 entry 可加载）
    src_manifest = get_plugin_frontend_dir(name) / "manifest.json"
    if src_manifest.is_file():
        try:
            with src_manifest.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("读取插件 %s 的 manifest.json 失败: %s", name, e)
            return None

    return None


def has_frontend(name: str) -> bool:
    """插件是否提供前端资源"""
    return read_frontend_manifest(name) is not None


def list_frontend_manifests(names: list[str]) -> list[dict[str, Any]]:
    """批量读取多个插件的前端 manifest

    Args:
        names: 已启用的插件名列表

    Returns:
        manifest 列表（跳过无前端或读取失败的插件）
    """
    out: list[dict[str, Any]] = []
    for name in names:
        # local_node 的前端逻辑已内置在主应用，不参与动态加载
        if name == "local_node":
            continue
        m = read_frontend_manifest(name)
        if m:
            out.append(m)
    return out
