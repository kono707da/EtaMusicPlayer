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
