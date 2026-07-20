"""网易云多账号 cookie 管理

每个账号一个 JSON 文件：accounts/<ncm_uid>.json
{
  "ncm_uid": "432838197",
  "nickname": "kono格子君",
  "avatar_url": "https://...",
  "vip_type": 0,
  "cookies": {"MUSIC_U": "...", "__csrf": "...", "NMTID": "..."},
  "last_login_at": "2026-07-20T18:05:11",
  "is_current": true
}

切换账号 = 加载对应 JSON，标记 is_current=true（其他账号设为 false）
新增账号 = 扫码登录成功后创建新 JSON
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("etamusic.plugins.netease")

# 当前账号 cookie（内存缓存，避免每次请求都读文件）
_current_account: Optional[dict] = None


def _accounts_dir() -> Path:
    """获取账号目录，确保存在"""
    p = Path(os.environ.get("NETEASE_ACCOUNTS_DIR", "accounts"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_accounts_dir(path: str | Path) -> None:
    """设置账号数据目录（由 plugin.py 启动时调用）"""
    os.environ["NETEASE_ACCOUNTS_DIR"] = str(path)
    Path(path).mkdir(parents=True, exist_ok=True)
    logger.info("网易云账号数据目录: %s", path)


def _account_file(ncm_uid: str) -> Path:
    return _accounts_dir() / f"{ncm_uid}.json"


def list_accounts() -> list[dict]:
    """列出所有账号（不含 cookies 字段，避免泄露）"""
    accounts = []
    for f in _accounts_dir().glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            accounts.append({
                "ncm_uid": data.get("ncm_uid"),
                "nickname": data.get("nickname"),
                "avatar_url": data.get("avatar_url"),
                "vip_type": data.get("vip_type"),
                "last_login_at": data.get("last_login_at"),
                "is_current": data.get("is_current", False),
            })
        except Exception as e:
            logger.warning("读取账号文件失败 %s: %s", f, e)
    return accounts


def get_account(ncm_uid: str) -> Optional[dict]:
    """读取账号完整数据（含 cookies）"""
    f = _account_file(ncm_uid)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("读取账号文件失败 %s: %s", f, e)
        return None


def save_account(ncm_uid: str, nickname: str, avatar_url: str, vip_type: int,
                 cookies: dict) -> dict:
    """保存或更新账号"""
    data = {
        "ncm_uid": str(ncm_uid),
        "nickname": nickname,
        "avatar_url": avatar_url,
        "vip_type": vip_type,
        "cookies": cookies,
        "last_login_at": datetime.now().isoformat(timespec="seconds"),
        "is_current": True,  # 新登录的自动设为当前
    }
    f = _account_file(str(ncm_uid))
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # 其他账号取消当前标记
    for other in _accounts_dir().glob("*.json"):
        if other == f:
            continue
        try:
            d = json.loads(other.read_text(encoding="utf-8"))
            if d.get("is_current"):
                d["is_current"] = False
                other.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    global _current_account
    _current_account = data
    logger.info("账号已保存: %s (%s)", nickname, ncm_uid)
    return data


def delete_account(ncm_uid: str) -> bool:
    """删除账号"""
    global _current_account
    f = _account_file(str(ncm_uid))
    if f.exists():
        f.unlink()
        if _current_account and _current_account.get("ncm_uid") == str(ncm_uid):
            _current_account = None
        logger.info("账号已删除: %s", ncm_uid)
        return True
    return False


def switch_account(ncm_uid: str) -> Optional[dict]:
    """切换当前账号"""
    global _current_account
    data = get_account(str(ncm_uid))
    if not data:
        return None
    # 取消其他账号的当前标记
    for f in _accounts_dir().glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            d["is_current"] = (d.get("ncm_uid") == str(ncm_uid))
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    _current_account = data
    logger.info("已切换到账号: %s (%s)", data.get("nickname"), ncm_uid)
    return data


def get_current_account() -> Optional[dict]:
    """获取当前账号（内存 → 文件）"""
    global _current_account
    if _current_account:
        return _current_account
    # 从文件找 is_current=True 的
    for f in _accounts_dir().glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("is_current"):
                _current_account = d
                return d
        except Exception:
            pass
    return None


def get_current_cookies() -> dict:
    """获取当前账号的 cookies，若无返回空 dict"""
    acc = get_current_account()
    if acc:
        return acc.get("cookies", {})
    return {}


def clear_current_cache() -> None:
    """清除内存缓存（切换/删除账号后调用）"""
    global _current_account
    _current_account = None
