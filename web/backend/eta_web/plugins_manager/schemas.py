"""插件管理 schemas"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PluginOut(BaseModel):
    """插件信息"""

    id: int
    name: str
    enabled: bool
    description: str
    version: str
    author: str
    installed_at: datetime
    updated_at: datetime
    loaded: bool = False
    files_present: bool = True

    model_config = {"from_attributes": True}


class PluginToggleResponse(BaseModel):
    name: str
    enabled: bool
    needs_restart: bool = True
    message: str = ""


class PluginDeleteResponse(BaseModel):
    name: str
    deleted: bool
    message: str = ""


class PluginRegistrySyncResponse(BaseModel):
    added: list[str] = []
    removed: list[str] = []
    updated: list[str] = []
    message: str = ""


class PluginRestartResponse(BaseModel):
    restarting: bool
    message: str = ""


class OnlinePluginInfo(BaseModel):
    """在线插件信息（合并本地状态）"""

    name: str
    package: str = ""
    display_name: str = ""
    description: str = ""
    online_version: Optional[str] = None
    local_version: Optional[str] = None
    author: str = ""
    eta_web_version: str = ""
    directory: str = ""
    category: str = "other"
    icon: str = "puzzle"
    online_available: bool = False
    installed: bool = False
    enabled: bool = False
    files_present: bool = False
    compatible: Optional[bool] = None
    compatibility_reason: str = ""
    can_install: bool = False
    can_update: bool = False
    update_available: bool = False


class PluginInstallResponse(BaseModel):
    success: bool
    message: str
    details: str = ""


class OnlineRegistryStatus(BaseModel):
    """在线注册表连接状态"""

    available: bool
    plugin_count: int = 0
    error: Optional[str] = None
    eta_web_version: str = ""
