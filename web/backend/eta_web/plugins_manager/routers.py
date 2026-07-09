"""插件管理 API 路由

挂在访问端骨架的 /api/plugins 下，不依赖任何插件。
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from eta_web.plugins_manager.database import get_db
from eta_web.plugins_manager.models import Plugin
from eta_web.plugins_manager.schemas import (
    OnlinePluginInfo,
    OnlineRegistryStatus,
    PluginDeleteResponse,
    PluginInstallResponse,
    PluginOut,
    PluginRegistrySyncResponse,
    PluginRestartResponse,
    PluginToggleResponse,
)
from eta_web.plugins_manager.manager import (
    delete_plugin_files,
    discover_plugins,
    sync_plugin_registry,
)
from eta_web.plugins_manager.online import registry as online_registry
from eta_web.plugins_manager.installer import install_plugin, update_plugin
from eta_web import __version__ as ETA_WEB_VERSION

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

_loaded_in_process: set[str] = set()


def set_loaded_plugins(names: list[str]) -> None:
    """供 main.py 调用，记录本次启动已加载的插件"""
    global _loaded_in_process
    _loaded_in_process = set(names)


@router.get("", response_model=list[PluginOut])
def list_plugins(db: Session = Depends(get_db)) -> list[PluginOut]:
    """列出所有已注册的插件（含启用状态与运行时加载状态）"""
    discovered = set(discover_plugins())
    rows = db.query(Plugin).order_by(Plugin.name).all()
    out: list[PluginOut] = []
    for r in rows:
        out.append(
            PluginOut(
                id=r.id,
                name=r.name,
                enabled=r.enabled,
                description=r.description,
                version=r.version,
                author=r.author,
                installed_at=r.installed_at,
                updated_at=r.updated_at,
                loaded=r.name in _loaded_in_process,
                files_present=r.name in discovered,
            )
        )
    return out


@router.post("/sync", response_model=PluginRegistrySyncResponse)
def sync_registry(db: Session = Depends(get_db)) -> PluginRegistrySyncResponse:
    """扫描插件目录，同步注册表

    新发现的插件会加入数据库（默认禁用）。已删除文件的插件会被禁用。
    """
    result = sync_plugin_registry(db)
    return PluginRegistrySyncResponse(
        added=result["added"],
        removed=result["removed"],
        updated=result["updated"],
        message=f"同步完成：新增 {len(result['added'])}，更新 {len(result['updated'])}，禁用 {len(result['removed'])}",
    )


@router.post("/{name}/enable", response_model=PluginToggleResponse)
def enable_plugin(name: str, db: Session = Depends(get_db)) -> PluginToggleResponse:
    """启用插件（需要重启访问端生效）"""
    plugin = db.query(Plugin).filter(Plugin.name == name).one_or_none()
    if plugin is None:
        raise HTTPException(status_code=404, detail="插件不存在")
    plugin.enabled = True
    db.commit()
    already_loaded = name in _loaded_in_process
    return PluginToggleResponse(
        name=name,
        enabled=True,
        needs_restart=not already_loaded,
        message="已启用，重启后生效" if not already_loaded else "已启用且当前已加载",
    )


@router.post("/{name}/disable", response_model=PluginToggleResponse)
def disable_plugin(name: str, db: Session = Depends(get_db)) -> PluginToggleResponse:
    """禁用插件（需要重启访问端生效）"""
    plugin = db.query(Plugin).filter(Plugin.name == name).one_or_none()
    if plugin is None:
        raise HTTPException(status_code=404, detail="插件不存在")
    plugin.enabled = False
    db.commit()
    still_loaded = name in _loaded_in_process
    return PluginToggleResponse(
        name=name,
        enabled=False,
        needs_restart=still_loaded,
        message="已禁用，重启后完全卸载" if still_loaded else "已禁用",
    )


@router.delete("/{name}", response_model=PluginDeleteResponse)
def delete_plugin(name: str, db: Session = Depends(get_db)) -> PluginDeleteResponse:
    """删除插件（删除文件 + 数据库记录）

    危险操作：会删除插件整个目录。
    """
    plugin = db.query(Plugin).filter(Plugin.name == name).one_or_none()
    if plugin is None:
        raise HTTPException(status_code=404, detail="插件不存在")
    if name in _loaded_in_process:
        raise HTTPException(
            status_code=400,
            detail="插件正在运行，请先禁用并重启访问端后再删除",
        )
    files_deleted = delete_plugin_files(name)
    db.delete(plugin)
    db.commit()
    return PluginDeleteResponse(
        name=name,
        deleted=True,
        message="已删除插件文件与记录" if files_deleted else "已删除数据库记录（文件已缺失）",
    )


# ===== 变更分析 + 服务器重启 =====

_RESTART_FLAG = Path(__file__).resolve().parents[2] / "data" / "restart.flag"


def _analyze_changes(
    db: Session, pending: dict[str, bool]
) -> dict:
    """分析待保存的变更是否需要重启服务器

    需要重启的场景：
    - 启用一个当前未加载的插件（要新加载它）
    - 禁用一个当前已加载的插件（要卸载它）

    不需要重启的场景：
    - 启用一个已加载的插件（no-op，运行时已是加载态）
    - 禁用一个未加载的插件（no-op，运行时本就没加载）
    - 插件文件缺失（无法加载，仅刷新数据库）

    返回 {needs_restart: bool, affected: [...], noop: [...]}
    """
    needs_restart = False
    affected: list[dict] = []
    noop: list[dict] = []

    for name, desired_enabled in pending.items():
        plugin = db.query(Plugin).filter(Plugin.name == name).one_or_none()
        if plugin is None:
            noop.append({"name": name, "reason": "插件不存在"})
            continue

        currently_loaded = name in _loaded_in_process
        currently_enabled = plugin.enabled

        if desired_enabled == currently_enabled:
            noop.append({"name": name, "reason": "状态未变"})
            continue

        if desired_enabled:
            if not currently_loaded:
                needs_restart = True
                affected.append({"name": name, "action": "enable", "reason": "需加载新插件"})
            else:
                noop.append({"name": name, "reason": "已加载，启用为 no-op"})
        else:
            if currently_loaded:
                needs_restart = True
                affected.append({"name": name, "action": "disable", "reason": "需卸载已加载插件"})
            else:
                noop.append({"name": name, "reason": "未加载，禁用为 no-op"})

    return {"needs_restart": needs_restart, "affected": affected, "noop": noop}


@router.post("/analyze-changes")
def analyze_changes(
    payload: dict, db: Session = Depends(get_db)
) -> dict:
    """分析待保存的变更是否需要重启服务器

    请求体：{ "changes": { "plugin_name": true/false, ... } }
    返回：{ needs_restart, affected, noop, message }
    """
    pending = payload.get("changes", {})
    if not pending:
        return {
            "needs_restart": False,
            "affected": [],
            "noop": [],
            "message": "无变更",
        }
    result = _analyze_changes(db, pending)
    if result["needs_restart"]:
        affected_desc = "，".join(
            f"{a['action']} {a['name']}" for a in result["affected"]
        )
        msg = f"以下变更需重启服务器：{affected_desc}"
    else:
        msg = "变更无需重启服务器，刷新页面即可生效"
    return {**result, "message": msg}


def _trigger_restart_delayed(delay: float = 1.5) -> None:
    """延迟写入重启标志并退出进程（在后台线程中执行）"""

    def _worker():
        time.sleep(delay)
        _RESTART_FLAG.parent.mkdir(parents=True, exist_ok=True)
        _RESTART_FLAG.write_text("restart", encoding="utf-8")
        os._exit(0)

    threading.Thread(target=_worker, daemon=True).start()


@router.post("/restart", response_model=PluginRestartResponse)
def restart_server() -> PluginRestartResponse:
    """触发访问端服务器重启

    1. 写入 data/restart.flag
    2. 延迟 1.5 秒后 os._exit(0) 退出当前进程
    3. run.py 检测到 flag 后重新启动 uvicorn

    前端调用此接口后应轮询 /health，待恢复后刷新页面。
    """
    _trigger_restart_delayed(1.5)
    return PluginRestartResponse(
        restarting=True,
        message="服务器将在 1.5 秒后重启，请等待 5-10 秒后刷新页面",
    )


@router.get("/local-node/status")
def local_node_status(db: Session = Depends(get_db)) -> dict:
    """查询本地节点插件的状态

    本地节点是本机固有的唯一节点，插件启用即自动连接，无需用户手动登录。
    本接口在插件可用时直接返回 admin 的 access_token，前端启动时自动写入 nodes store。

    返回：
    - available: 本地节点插件是否已安装且启用
    - loaded: 是否在当前进程中已加载
    - base_url: 访问本地节点的相对路径（如 /local_node）
    - access_token: admin 用户的 JWT（仅当 available=true 时返回）
    - user_info: admin 用户信息
    """
    plugin = db.query(Plugin).filter(Plugin.name == "local_node").one_or_none()
    if plugin is None:
        return {
            "available": False,
            "loaded": False,
            "base_url": None,
            "message": "本地节点插件未安装",
        }
    discovered = set(discover_plugins())
    files_present = plugin.name in discovered
    available = plugin.enabled and files_present
    loaded = "local_node" in _loaded_in_process

    result = {
        "available": available,
        "loaded": loaded,
        "base_url": "/local_node" if plugin.enabled else None,
        "name": "本地节点",
        "description": plugin.description,
        "version": plugin.version,
        "message": "" if plugin.enabled else "本地节点插件未启用",
    }

    if available and loaded:
        try:
            from eta_web.security import create_access_token
            from eta_node.database import SessionLocal as LocalSession
            from eta_node.models import User as LocalUser
        except ImportError:
            pass
        else:
            local_db = LocalSession()
            try:
                admin = local_db.query(LocalUser).filter(LocalUser.username == "admin").one_or_none()
                if admin:
                    token = create_access_token(admin.id)
                    result["access_token"] = token
                    result["user_info"] = {
                        "id": admin.id,
                        "username": admin.username,
                        "is_admin": admin.is_admin,
                    }
            finally:
                local_db.close()

    return result


# ===== 在线插件注册表 =====


@router.get("/online", response_model=list[OnlinePluginInfo])
def list_online_plugins(db: Session = Depends(get_db)) -> list[OnlinePluginInfo]:
    """获取在线插件列表（合并本地安装状态和版本兼容性）

    从 GitHub plugins.json 获取在线插件信息，与本地已安装插件对比，
    返回每个插件的安装状态、版本差异和兼容性检查结果。
    """
    discovered = set(discover_plugins())
    rows = db.query(Plugin).order_by(Plugin.name).all()
    local_plugins = [
        {
            "name": r.name,
            "version": r.version,
            "enabled": r.enabled,
            "files_present": r.name in discovered,
        }
        for r in rows
    ]

    merged = online_registry.compare_with_local(local_plugins)
    return [OnlinePluginInfo(**p) for p in merged]


@router.get("/online/status", response_model=OnlineRegistryStatus)
def online_registry_status() -> OnlineRegistryStatus:
    """检查在线注册表连接状态"""
    try:
        plugins = online_registry.fetch_plugins()
        return OnlineRegistryStatus(
            available=True,
            plugin_count=len(plugins),
            eta_web_version=ETA_WEB_VERSION,
        )
    except (ConnectionError, ValueError) as e:
        return OnlineRegistryStatus(
            available=False,
            plugin_count=0,
            error=str(e),
            eta_web_version=ETA_WEB_VERSION,
        )


@router.post("/online/refresh")
def refresh_online_registry() -> dict:
    """强制刷新在线注册表缓存"""
    try:
        plugins = online_registry.fetch_plugins(force=True)
        return {
            "success": True,
            "count": len(plugins),
            "message": f"已刷新在线注册表，获取到 {len(plugins)} 个插件",
        }
    except (ConnectionError, ValueError) as e:
        raise HTTPException(status_code=502, detail=f"无法连接在线注册表: {e}")


@router.post("/online/{name}/install", response_model=PluginInstallResponse)
def install_online_plugin(name: str) -> PluginInstallResponse:
    """从在线注册表安装插件

    流程：下载仓库 zip → 解压插件目录 → 安装依赖 → 同步注册表
    安装后需要重启服务才能加载新插件。
    """
    result = install_plugin(name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return PluginInstallResponse(**result)


@router.post("/online/{name}/update", response_model=PluginInstallResponse)
def update_online_plugin(name: str) -> PluginInstallResponse:
    """从在线注册表更新插件

    流程与安装相同，但会覆盖已安装的插件目录。
    更新后需要重启服务才能生效。
    """
    result = update_plugin(name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return PluginInstallResponse(**result)
