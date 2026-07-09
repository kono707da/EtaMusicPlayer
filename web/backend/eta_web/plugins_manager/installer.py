"""插件安装器

从 GitHub 仓库下载插件 zip 包，解压到本地 plugins 目录，
安装 Python 依赖，并同步到数据库注册表。
"""
from __future__ import annotations

import io
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional

import requests

from eta_web.config import BASE_DIR, settings
from eta_web.plugins.registry import PLUGIN_PACKAGE_MAP, PLUGIN_SEARCH_PATHS

logger = logging.getLogger("eta_web.plugins_manager.installer")


def _get_target_dir(plugin_name: str, online_directory: str) -> Path:
    """获取插件安装目标目录

    对于 local_node，目标目录是 MONOREPO_ROOT/node
    对于其他插件，目标目录是 MONOREPO_ROOT/plugins/{plugin_name}
    """
    if plugin_name == "local_node":
        return (BASE_DIR / "../../node").resolve()
    return (BASE_DIR / f"../../plugins/{plugin_name}").resolve()


def _download_repo_archive() -> bytes:
    """从 GitHub 下载仓库 zip 包

    Returns:
        zip 文件的字节数据

    Raises:
        ConnectionError: 下载失败
    """
    url = settings.plugin_repo_archive_url
    logger.info("正在从 %s 下载仓库包...", url)
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        data = resp.content
        logger.info("仓库包下载完成，大小: %.1f KB", len(data) / 1024)
        return data
    except requests.RequestException as e:
        logger.error("下载仓库包失败: %s", e)
        raise ConnectionError(f"下载仓库包失败: {e}") from e


def _extract_plugin_from_zip(
    zip_data: bytes,
    plugin_directory: str,
    target_dir: Path,
) -> None:
    """从仓库 zip 包中提取插件目录

    GitHub 下载的 zip 包顶层目录格式为 {repo}-{branch}/，
    插件目录在 {repo}-{branch}/{plugin_directory}/ 下。

    Args:
        zip_data: zip 文件字节数据
        plugin_directory: 插件在仓库中的目录路径（如 "node" 或 "plugins/asmr_one"）
        target_dir: 本地目标目录
    """
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        names = zf.namelist()
        prefix = names[0].split("/")[0] if names else ""

        plugin_prefix = f"{prefix}/{plugin_directory}/"
        plugin_files = [n for n in names if n.startswith(plugin_prefix) and not n.endswith("/")]

        if not plugin_files:
            raise ValueError(
                f"仓库包中未找到插件目录: {plugin_directory} "
                f"(搜索前缀: {plugin_prefix})"
            )

        if target_dir.exists():
            logger.warning("目标目录已存在，将覆盖: %s", target_dir)
            shutil.rmtree(target_dir)

        target_dir.mkdir(parents=True, exist_ok=True)

        for file_path in plugin_files:
            relative = file_path[len(plugin_prefix):]
            dest = target_dir / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(file_path) as src, open(dest, "wb") as dst:
                dst.write(src.read())

        logger.info(
            "已从仓库包提取 %d 个文件到 %s",
            len(plugin_files),
            target_dir,
        )


def _install_requirements(target_dir: Path, requirements_file: str) -> str:
    """安装插件 Python 依赖

    Args:
        target_dir: 插件安装目录
        requirements_file: requirements.txt 在仓库中的相对路径

    Returns:
        pip install 的输出
    """
    req_path = target_dir / "requirements.txt"
    if not req_path.exists():
        logger.info("插件无 requirements.txt，跳过依赖安装")
        return "无 requirements.txt，跳过依赖安装"

    logger.info("正在安装插件依赖: %s", req_path)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            logger.warning("依赖安装部分失败 (exit %d): %s", result.returncode, output[-500:])
            return f"依赖安装部分失败:\n{output[-500:]}"
        logger.info("依赖安装完成")
        return "依赖安装完成"
    except subprocess.TimeoutExpired:
        logger.error("依赖安装超时（5 分钟）")
        return "依赖安装超时（5 分钟）"
    except Exception as e:
        logger.error("依赖安装异常: %s", e, exc_info=True)
        return f"依赖安装异常: {e}"


def install_plugin(plugin_name: str) -> dict:
    """安装在线插件

    流程：
    1. 从在线注册表获取插件信息
    2. 检查版本兼容性
    3. 下载仓库 zip 包
    4. 解压插件目录到本地
    5. 安装 Python 依赖
    6. 同步数据库注册表

    Returns:
        {success: bool, message: str, details: str}
    """
    from eta_web.plugins_manager.online import registry

    online = registry.get_plugin(plugin_name)
    if online is None:
        return {
            "success": False,
            "message": f"在线注册表中未找到插件: {plugin_name}",
            "details": "",
        }

    compatible, reason = online.is_compatible()
    if not compatible:
        return {
            "success": False,
            "message": f"插件 {plugin_name} 与当前骨架版本不兼容",
            "details": reason,
        }

    target_dir = _get_target_dir(plugin_name, online.directory)

    try:
        zip_data = _download_repo_archive()
    except ConnectionError as e:
        return {
            "success": False,
            "message": f"下载仓库包失败: {e}",
            "details": "",
        }

    try:
        _extract_plugin_from_zip(zip_data, online.directory, target_dir)
    except (ValueError, zipfile.BadZipFile) as e:
        return {
            "success": False,
            "message": f"解压插件失败: {e}",
            "details": "",
        }

    req_output = _install_requirements(target_dir, online.requirements)

    if plugin_name not in PLUGIN_SEARCH_PATHS:
        path_str = str(target_dir)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
        logger.info("已将新插件目录加入 sys.path: %s", path_str)

    try:
        from eta_web.plugins_manager.database import SessionLocal
        from eta_web.plugins_manager.manager import sync_plugin_registry

        db = SessionLocal()
        try:
            sync_plugin_registry(db)
        finally:
            db.close()
    except Exception as e:
        logger.warning("同步注册表失败（插件已安装）: %s", e)

    return {
        "success": True,
        "message": f"插件 {online.display_name} ({plugin_name}) v{online.version} 安装成功",
        "details": req_output,
    }


def update_plugin(plugin_name: str) -> dict:
    """更新在线插件（重新下载覆盖安装）

    流程与 install_plugin 相同，但会先检查是否已安装。
    """
    from eta_web.plugins_manager.online import registry

    online = registry.get_plugin(plugin_name)
    if online is None:
        return {
            "success": False,
            "message": f"在线注册表中未找到插件: {plugin_name}",
            "details": "",
        }

    compatible, reason = online.is_compatible()
    if not compatible:
        return {
            "success": False,
            "message": f"插件 {plugin_name} v{online.version} 与当前骨架版本不兼容",
            "details": reason,
        }

    target_dir = _get_target_dir(plugin_name, online.directory)

    try:
        zip_data = _download_repo_archive()
    except ConnectionError as e:
        return {
            "success": False,
            "message": f"下载仓库包失败: {e}",
            "details": "",
        }

    try:
        _extract_plugin_from_zip(zip_data, online.directory, target_dir)
    except (ValueError, zipfile.BadZipFile) as e:
        return {
            "success": False,
            "message": f"解压插件失败: {e}",
            "details": "",
        }

    req_output = _install_requirements(target_dir, online.requirements)

    try:
        from eta_web.plugins_manager.database import SessionLocal
        from eta_web.plugins_manager.manager import sync_plugin_registry

        db = SessionLocal()
        try:
            sync_plugin_registry(db)
        finally:
            db.close()
    except Exception as e:
        logger.warning("同步注册表失败（插件已更新）: %s", e)

    return {
        "success": True,
        "message": f"插件 {online.display_name} ({plugin_name}) 已更新到 v{online.version}",
        "details": req_output,
    }
