"""配置加载模块

使用 pydantic-settings 从 config.yaml 加载配置。
运行时密钥（jwt_secret）自动生成并持久化到 data/settings.json。
"""
from __future__ import annotations

import json
import logging
import os
import secrets
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

logger = logging.getLogger("eta_web")

BASE_DIR = Path(__file__).resolve().parent.parent

SETTINGS_JSON_PATH = BASE_DIR / "data" / "settings.json"


class Settings(BaseModel):
    """应用配置模型"""

    host: str = "127.0.0.1"
    port: int = 8000
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    plugins_dirs: list[str] = [
        "../../node",
        "../../plugins/asmr_one",
        "../../plugins/bili_audio",
    ]
    plugins_enabled: list[str] = ["local_node", "bili_audio"]
    plugin_registry_url: str = "https://raw.githubusercontent.com/kono707da/EtaMusicPlayer/main/plugins.json"
    plugin_repo_archive_url: str = "https://github.com/kono707da/EtaMusicPlayer/archive/refs/heads/main.zip"


def _load_yaml() -> dict[str, Any]:
    """读取 config.yaml"""
    cfg_file = BASE_DIR / "config.yaml"
    if not cfg_file.exists():
        return {}
    with cfg_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def _load_settings_json() -> dict[str, Any]:
    """读取 data/settings.json（运行时持久化配置）"""
    if not SETTINGS_JSON_PATH.exists():
        return {}
    try:
        with SETTINGS_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("读取 settings.json 失败，将重新生成: %s", exc)
        return {}


def _save_settings_json(data: dict[str, Any]) -> None:
    """写入 data/settings.json"""
    SETTINGS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _ensure_jwt_secret(persisted: dict[str, Any]) -> str:
    """确保 jwt_secret 存在，不存在则自动生成并持久化

    优先级：settings.json 已保存值 > 自动生成新值
    不再从 config.yaml 或环境变量读取。
    """
    existing = persisted.get("jwt_secret")
    if existing and isinstance(existing, str) and existing.strip():
        return existing.strip()

    new_secret = secrets.token_urlsafe(48)
    persisted["jwt_secret"] = new_secret
    _save_settings_json(persisted)
    logger.info("已自动生成 JWT 密钥并保存到 %s", SETTINGS_JSON_PATH)
    return new_secret


def load_settings() -> Settings:
    """从 config.yaml + data/settings.json 加载配置，环境变量 ETA_WEB_ 前缀可覆盖（jwt_secret 除外）"""
    yaml_data = _load_yaml()
    yaml_data.pop("jwt_secret", None)

    env_overrides: dict[str, Any] = {}
    for key in Settings.model_fields:
        if key == "jwt_secret":
            continue
        env_key = f"ETA_WEB_{key.upper()}"
        if env_key in os.environ:
            env_overrides[key] = os.environ[env_key]

    persisted = _load_settings_json()
    jwt_secret = _ensure_jwt_secret(persisted)

    merged = {**yaml_data, **env_overrides, "jwt_secret": jwt_secret}
    return Settings(**merged)


settings = load_settings()
