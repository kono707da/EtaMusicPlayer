"""EtaMusic Node 配置"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic_settings import BaseSettings


def _load_yaml_config() -> dict:
    config_paths = [
        Path(__file__).resolve().parent.parent / "config.yaml",
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
        return Path(__file__).resolve().parent.parent / p

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
