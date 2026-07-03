"""配置加载模块

使用 pydantic-settings 从 config.yaml 加载配置。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


# backend 目录的绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """应用配置模型"""

    host: str = "127.0.0.1"
    port: int = 8000
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 1440
    scan_workers: int = 2
    db_path: str = "data/etamusic.db"
    default_admin_password: str = "admin123"
    # 已启用的插件列表
    plugins_enabled: list[str] = ["local_node"]
    # 访问端对外可达地址（供插件/前端发现用）
    self_url: str = "http://127.0.0.1:8000"

    @property
    def db_absolute_path(self) -> Path:
        """数据库绝对路径，自动创建父目录"""
        p = Path(self.db_path)
        if not p.is_absolute():
            p = BASE_DIR / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def database_url(self) -> str:
        """SQLAlchemy 连接串"""
        return f"sqlite:///{self.db_absolute_path.as_posix()}"


def _load_yaml() -> dict[str, Any]:
    """读取 config.yaml"""
    cfg_file = BASE_DIR / "config.yaml"
    if not cfg_file.exists():
        return {}
    with cfg_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def load_settings() -> Settings:
    """从 config.yaml 加载配置，环境变量 ETA_ 前缀可覆盖"""
    data = _load_yaml()
    # 环境变量覆盖（ETA_HOST、ETA_PORT 等）
    env_overrides: dict[str, Any] = {}
    for key in Settings.model_fields:
        env_key = f"ETA_{key.upper()}"
        if env_key in os.environ:
            env_overrides[key] = os.environ[env_key]
    merged = {**data, **env_overrides}
    return Settings(**merged)


settings = load_settings()
