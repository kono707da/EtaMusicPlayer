"""在线插件注册表客户端

从 GitHub 仓库获取 plugins.json 索引，解析可用插件列表，
并与本地已安装插件进行版本对比和兼容性检查。
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import requests
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

from eta_web import __version__ as ETA_WEB_VERSION
from eta_web.config import BASE_DIR, settings

logger = logging.getLogger("eta_web.plugins_manager.online")


class OnlinePlugin:
    """在线插件信息"""

    def __init__(self, data: dict) -> None:
        self.name: str = data.get("name", "")
        self.package: str = data.get("package", "")
        self.display_name: str = data.get("display_name", self.name)
        self.description: str = data.get("description", "")
        self.version: str = data.get("version", "0.0.0")
        self.author: str = data.get("author", "")
        self.eta_web_version: str = data.get("eta_web_version", "")
        self.directory: str = data.get("directory", "")
        self.entry: str = data.get("entry", "")
        self.requirements: str = data.get("requirements", "")
        self.category: str = data.get("category", "other")
        self.icon: str = data.get("icon", "puzzle")
        # schema v2 新增字段
        self.type: str = data.get("type", "plugin")  # "plugin" | "library"
        self.dependencies: list[dict] = data.get("dependencies", []) or []
        self.sha256: str = data.get("sha256", "")

    @property
    def is_library(self) -> bool:
        """是否为库类型（无 plugin.py，不注册路由，仅提供 import 支持）"""
        return self.type == "library"

    @property
    def dependency_names(self) -> list[str]:
        """依赖的插件名列表"""
        return [d.get("name", "") for d in self.dependencies if d.get("name")]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "package": self.package,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "eta_web_version": self.eta_web_version,
            "directory": self.directory,
            "entry": self.entry,
            "requirements": self.requirements,
            "category": self.category,
            "icon": self.icon,
            "type": self.type,
            "dependencies": self.dependencies,
            "sha256": self.sha256,
        }

    def is_compatible(self) -> tuple[bool, str]:
        """检查当前访问端版本是否兼容此插件

        返回 (compatible, reason)
        """
        if not self.eta_web_version:
            return True, "未声明版本要求"
        try:
            spec = SpecifierSet(self.eta_web_version)
            current = Version(ETA_WEB_VERSION)
            if current in spec:
                return True, f"兼容 (访问端 {ETA_WEB_VERSION} 满足 {self.eta_web_version})"
            return False, f"不兼容 (访问端 {ETA_WEB_VERSION} 不满足 {self.eta_web_version})"
        except (InvalidVersion, Exception) as e:
            return False, f"版本约束解析失败: {e}"


class OnlineRegistry:
    """在线插件注册表"""

    def __init__(self) -> None:
        self._cache: Optional[list[OnlinePlugin]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 300  # 5 分钟缓存

    @property
    def _registry_url(self) -> str:
        return settings.plugin_registry_url

    @property
    def _repo_archive_url(self) -> str:
        return settings.plugin_repo_archive_url

    def _is_cache_valid(self) -> bool:
        if self._cache is None or self._cache_time is None:
            return False
        elapsed = (datetime.utcnow() - self._cache_time).total_seconds()
        return elapsed < self._cache_ttl

    def fetch_plugins(self, force: bool = False) -> list[OnlinePlugin]:
        """从 GitHub 获取在线插件列表

        Args:
            force: 是否强制刷新缓存

        Returns:
            在线插件列表

        Raises:
            ConnectionError: 网络连接失败
            ValueError: plugins.json 格式错误
        """
        if not force and self._is_cache_valid():
            return self._cache

        try:
            resp = requests.get(
                self._registry_url,
                timeout=15,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
        except requests.ConnectionError as e:
            logger.error("无法连接插件注册表: %s", e)
            raise ConnectionError(f"无法连接插件注册表: {e}") from e
        except requests.HTTPError as e:
            logger.error("插件注册表返回错误: %s", e)
            raise ConnectionError(f"插件注册表返回错误: {e}") from e
        except requests.Timeout:
            logger.error("插件注册表请求超时")
            raise ConnectionError("插件注册表请求超时")

        try:
            data = resp.json()
        except ValueError as e:
            logger.error("plugins.json 解析失败: %s", e)
            raise ValueError(f"plugins.json 解析失败: {e}") from e

        schema_version = data.get("schema_version", 0)
        if schema_version < 1:
            raise ValueError(f"不支持的 plugins.json schema_version: {schema_version}")

        plugins_data = data.get("plugins", [])
        plugins = [OnlinePlugin(p) for p in plugins_data]

        self._cache = plugins
        self._cache_time = datetime.utcnow()
        logger.info("从在线注册表获取到 %d 个插件", len(plugins))
        return plugins

    def get_plugin(self, name: str) -> Optional[OnlinePlugin]:
        """按名称获取在线插件信息"""
        try:
            plugins = self.fetch_plugins()
        except (ConnectionError, ValueError):
            return None
        for p in plugins:
            if p.name == name:
                return p
        return None

    def compare_with_local(
        self, local_plugins: list[dict]
    ) -> list[dict]:
        """对比在线插件与本地已安装插件

        Args:
            local_plugins: 本地插件列表，每项含 name, version, enabled, files_present

        Returns:
            合并后的插件信息列表，每项含：
            - 在线信息 (online_version, display_name, category, icon, compatible, compatibility_reason)
            - 本地信息 (installed, local_version, enabled, files_present)
            - 状态 (can_install, can_update, update_available)
        """
        try:
            online_plugins = self.fetch_plugins()
        except (ConnectionError, ValueError) as e:
            logger.warning("无法获取在线插件列表: %s", e)
            return [
                {
                    **lp,
                    "online_available": False,
                    "online_version": None,
                    "display_name": lp.get("name", ""),
                    "category": "unknown",
                    "icon": "puzzle",
                    "compatible": None,
                    "compatibility_reason": "无法连接在线注册表",
                    "can_install": False,
                    "can_update": False,
                    "update_available": False,
                }
                for lp in local_plugins
            ]

        online_map = {p.name: p for p in online_plugins}
        local_map = {lp["name"]: lp for lp in local_plugins}

        result: list[dict] = []

        for op in online_plugins:
            compatible, reason = op.is_compatible()
            local = local_map.get(op.name)
            installed = local is not None and local.get("files_present", False)

            update_available = False
            local_version = None
            enabled = False
            if local:
                local_version = local.get("version", "0.0.0")
                enabled = local.get("enabled", False)
                try:
                    update_available = Version(op.version) > Version(local_version)
                except (InvalidVersion, Exception):
                    update_available = op.version != local_version

            result.append({
                "name": op.name,
                "package": op.package,
                "display_name": op.display_name,
                "description": op.description,
                "online_version": op.version,
                "author": op.author,
                "eta_web_version": op.eta_web_version,
                "directory": op.directory,
                "category": op.category,
                "icon": op.icon,
                "type": op.type,
                "dependencies": op.dependencies,
                "is_library": op.is_library,
                "online_available": True,
                "installed": installed,
                "local_version": local_version,
                "enabled": enabled,
                "files_present": local.get("files_present", False) if local else False,
                "compatible": compatible,
                "compatibility_reason": reason,
                "can_install": not installed and compatible,
                "can_update": installed and update_available and compatible,
                "update_available": update_available,
            })

        for lp in local_plugins:
            if lp["name"] not in online_map:
                result.append({
                    "name": lp["name"],
                    "package": "",
                    "display_name": lp.get("name", ""),
                    "description": lp.get("description", ""),
                    "online_version": None,
                    "author": lp.get("author", ""),
                    "eta_web_version": "",
                    "directory": "",
                    "category": "unknown",
                    "icon": "puzzle",
                    "online_available": False,
                    "installed": True,
                    "local_version": lp.get("version", "0.0.0"),
                    "enabled": lp.get("enabled", False),
                    "files_present": lp.get("files_present", False),
                    "compatible": None,
                    "compatibility_reason": "仅本地安装，在线注册表中不存在",
                    "can_install": False,
                    "can_update": False,
                    "update_available": False,
                })

        return result


registry = OnlineRegistry()
