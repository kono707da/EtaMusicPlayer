"""EtaMusic Node 配置"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings


def _get_base_dir() -> Path:
    """获取运行时基础目录

    - 开发模式: eta_node 包的上级目录 (node/)
    - PyInstaller onedir: exe 所在目录
    - PyInstaller onefile: 临时解压目录
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()


def _load_yaml_config() -> dict:
    config_paths = [
        BASE_DIR / "config.yaml",
        Path("config.yaml"),
    ]
    for p in config_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


_yaml_config = _load_yaml_config()


class NodeSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001
    db_path: str = "data/etamusic.db"
    staging_dir: str = "data/staging"
    scan_workers: int = 2
    default_admin_password: str = "admin123"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    model_config = {"env_prefix": "ETA_NODE_"}

    @property
    def db_absolute_path(self) -> Path:
        p = Path(self.db_path)
        if p.is_absolute():
            return p
        return BASE_DIR / p

    @property
    def staging_absolute_path(self) -> Path:
        p = Path(self.staging_dir)
        if p.is_absolute():
            return p
        return BASE_DIR / p

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_absolute_path.as_posix()}"


_settings: Optional[NodeSettings] = None


def get_settings() -> NodeSettings:
    global _settings
    if _settings is None:
        _settings = NodeSettings(**{k: v for k, v in _yaml_config.items() if v is not None})
    return _settings


def configure(**kwargs) -> None:
    global _settings
    _settings = NodeSettings(**kwargs)


settings = get_settings()
