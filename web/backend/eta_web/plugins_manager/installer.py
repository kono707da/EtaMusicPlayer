"""插件安装器

支持：
- 在线安装（从 GitHub 仓库下载，一次下载提取多个插件+依赖）
- 手动导入（上传 zip，Phase 3 实现）
- 依赖解析（自动安装依赖，去重保留一份，版本冲突时更新）
- SHA256 校验（手动导入时）
- 元数据校验（结构验证）
- 路径穿越防护
- 备份与回滚
"""
from __future__ import annotations

import hashlib
import io
import logging
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional

import requests
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

from eta_web.config import BASE_DIR, settings
from eta_web.plugins.registry import (
    PLUGIN_PACKAGE_MAP,
    PLUGIN_SEARCH_PATHS,
    add_plugin_path,
    refresh_plugin_paths,
)

logger = logging.getLogger("eta_web.plugins_manager.installer")


def _get_target_dir(plugin_name: str, online_directory: str = "") -> Path:
    """获取插件安装目标目录

    local_node → ../../node/
    其他 → ../../plugins/{plugin_name}/
    """
    if plugin_name == "local_node":
        return (BASE_DIR / "../../node").resolve()
    return (BASE_DIR / f"../../plugins/{plugin_name}").resolve()


def _compute_sha256(data: bytes) -> str:
    """计算字节数据的 SHA256"""
    return hashlib.sha256(data).hexdigest()


def _validate_zip_paths(zf: zipfile.ZipFile) -> None:
    """校验 zip 中的路径，防止路径穿越攻击

    Raises:
        ValueError: 发现危险路径
    """
    for name in zf.namelist():
        # 绝对路径（Windows 和 Unix）
        if name.startswith("/") or name.startswith("\\"):
            raise ValueError(f"非法路径（绝对路径）: {name}")
        # Windows 盘符
        if len(name) >= 2 and name[1] == ":":
            raise ValueError(f"非法路径（盘符）: {name}")
        # 路径穿越
        parts = name.replace("\\", "/").split("/")
        if ".." in parts:
            raise ValueError(f"非法路径（路径穿越）: {name}")


def _backup_plugin(target_dir: Path) -> Optional[Path]:
    """备份现有插件目录"""
    if not target_dir.exists():
        return None
    backup = target_dir.parent / f".{target_dir.name}.bak"
    if backup.exists():
        shutil.rmtree(backup)
    shutil.move(str(target_dir), str(backup))
    logger.info("已备份插件目录: %s -> %s", target_dir.name, backup)
    return backup


def _restore_backup(backup_dir: Optional[Path], target_dir: Path) -> None:
    """从备份恢复插件目录"""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    if backup_dir and backup_dir.exists():
        shutil.move(str(backup_dir), str(target_dir))
        logger.info("已从备份恢复: %s", target_dir.name)
    else:
        logger.warning("无备份可恢复，目标目录已清空: %s", target_dir)


def _cleanup_backup(backup_dir: Optional[Path]) -> None:
    """清理备份目录"""
    if backup_dir and backup_dir.exists():
        shutil.rmtree(backup_dir)
        logger.debug("已清理备份: %s", backup_dir)


def _download_repo_archive() -> bytes:
    """从 GitHub 下载仓库 zip 包"""
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


def _extract_plugin_from_repo_zip(
    zip_data: bytes,
    plugin_directory: str,
    target_dir: Path,
) -> None:
    """从仓库 zip 包中提取插件目录（带路径穿越防护）

    GitHub zip 顶层格式为 {repo}-{branch}/，插件目录在 {repo}-{branch}/{plugin_directory}/ 下。
    """
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        _validate_zip_paths(zf)
        names = zf.namelist()
        prefix = names[0].split("/")[0] if names else ""

        plugin_prefix = f"{prefix}/{plugin_directory}/"
        plugin_files = [n for n in names if n.startswith(plugin_prefix) and not n.endswith("/")]

        if not plugin_files:
            raise ValueError(
                f"仓库包中未找到插件目录: {plugin_directory} (搜索前缀: {plugin_prefix})"
            )

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        for file_path in plugin_files:
            relative = file_path[len(plugin_prefix):]
            dest = target_dir / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(file_path) as src, open(dest, "wb") as dst:
                dst.write(src.read())

        logger.info("已从仓库包提取 %d 个文件到 %s", len(plugin_files), target_dir.name)


def _validate_plugin_structure(
    target_dir: Path, package_name: str, is_library: bool = False
) -> None:
    """验证插件目录结构

    Raises:
        ValueError: 结构不合法
    """
    if not target_dir.exists():
        raise ValueError(f"插件目录不存在: {target_dir}")

    package_dir = target_dir / package_name
    if not package_dir.exists():
        raise ValueError(f"包目录不存在: {package_name}/")

    if not (package_dir / "__init__.py").exists():
        raise ValueError(f"缺少 {package_name}/__init__.py")

    if not is_library:
        if not (package_dir / "plugin.py").exists():
            raise ValueError(f"缺少 {package_name}/plugin.py（普通插件必须包含此文件）")


def _install_requirements(target_dir: Path) -> str:
    """安装插件 Python 依赖"""
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


def _check_dependency_installed(
    dep_name: str, dep_version_spec: str
) -> tuple[bool, bool, str]:
    """检查依赖插件是否已安装且版本兼容

    Returns:
        (installed, compatible, current_version)
    """
    from eta_web.plugins_manager.database import SessionLocal
    from eta_web.plugins_manager.manager import discover_plugins
    from eta_web.plugins_manager.models import Plugin

    db = SessionLocal()
    try:
        plugin = db.query(Plugin).filter(Plugin.name == dep_name).one_or_none()
        if plugin is None:
            return False, False, ""

        discovered = set(discover_plugins())
        if dep_name not in discovered:
            return False, False, plugin.version

        if not dep_version_spec:
            return True, True, plugin.version

        try:
            spec = SpecifierSet(dep_version_spec)
            current = Version(plugin.version)
            return True, current in spec, plugin.version
        except (InvalidVersion, Exception):
            return True, True, plugin.version
    finally:
        db.close()


def _install_single_plugin(
    zip_data: bytes,
    online,
    backup_map: dict[str, Path],
) -> None:
    """从已下载的仓库 zip 中提取并安装单个插件

    Args:
        zip_data: 仓库 zip 字节数据
        online: OnlinePlugin 实例
        backup_map: 备份目录映射（插件名 -> 备份路径），用于回滚
    """
    target_dir = _get_target_dir(online.name, online.directory)

    if target_dir.exists():
        backup_map[online.name] = _backup_plugin(target_dir)

    _extract_plugin_from_repo_zip(zip_data, online.directory, target_dir)
    _validate_plugin_structure(target_dir, online.package, online.is_library)
    add_plugin_path(online.name, target_dir, online.package)


def install_plugin(plugin_name: str) -> dict:
    """安装在线插件（含依赖解析）

    流程：
    1. 从在线注册表获取插件信息
    2. 检查版本兼容性
    3. 解析依赖：未安装或版本不兼容的依赖需要安装
    4. 下载仓库 zip 包（一次下载）
    5. 依次安装依赖和主插件
    6. 安装 Python 依赖
    7. 同步数据库注册表
    8. 更新依赖关系（dependent_by）

    Returns:
        {success, message, details, dependencies_installed}
    """
    from eta_web.plugins_manager.online import registry as online_registry
    from eta_web.plugins_manager.database import SessionLocal
    from eta_web.plugins_manager.manager import sync_plugin_registry, update_dependent_by

    online = online_registry.get_plugin(plugin_name)
    if online is None:
        return {"success": False, "message": f"在线注册表中未找到插件: {plugin_name}", "details": ""}

    compatible, reason = online.is_compatible()
    if not compatible:
        return {"success": False, "message": f"插件 {plugin_name} 与当前访问端版本不兼容", "details": reason}

    # 解析依赖
    deps_to_install: list = []  # OnlinePlugin 列表
    for dep in online.dependencies:
        dep_name = dep.get("name", "")
        dep_version = dep.get("version", "")
        if not dep_name:
            continue

        installed, compatible_dep, current_ver = _check_dependency_installed(dep_name, dep_version)

        if installed and compatible_dep:
            logger.info("依赖 %s 已安装且版本兼容 (v%s)，跳过", dep_name, current_ver)
            # 更新依赖关系
            db = SessionLocal()
            try:
                update_dependent_by(db, dep_name, plugin_name, add=True)
            finally:
                db.close()
            continue

        if installed and not compatible_dep:
            logger.info("依赖 %s 已安装但版本不兼容 (当前 v%s, 需要 %s)，将更新", dep_name, current_ver, dep_version)

        dep_online = online_registry.get_plugin(dep_name)
        if dep_online is None:
            return {
                "success": False,
                "message": f"在线注册表中未找到依赖插件: {dep_name}",
                "details": "",
            }
        dep_compatible, dep_reason = dep_online.is_compatible()
        if not dep_compatible:
            return {
                "success": False,
                "message": f"依赖 {dep_name} 与当前访问端版本不兼容",
                "details": dep_reason,
            }
        deps_to_install.append(dep_online)

    # 下载仓库 zip（一次下载，提取多个插件）
    try:
        zip_data = _download_repo_archive()
    except ConnectionError as e:
        return {"success": False, "message": f"下载仓库包失败: {e}", "details": ""}

    backup_map: dict[str, Path] = {}
    installed_names: list[str] = []

    # 安装依赖
    for dep_online in deps_to_install:
        try:
            _install_single_plugin(zip_data, dep_online, backup_map)
            installed_names.append(dep_online.name)
            logger.info("依赖插件 %s 安装成功", dep_online.name)
        except Exception as e:
            logger.error("安装依赖 %s 失败: %s", dep_online.name, e)
            # 回滚已安装的依赖
            for name in installed_names:
                _restore_backup(backup_map.get(name), _get_target_dir(name))
            return {
                "success": False,
                "message": f"安装依赖 {dep_online.name} 失败: {e}",
                "details": "",
            }

    # 安装主插件
    try:
        _install_single_plugin(zip_data, online, backup_map)
    except (ValueError, zipfile.BadZipFile) as e:
        # 回滚所有已安装的插件
        for name in installed_names:
            _restore_backup(backup_map.get(name), _get_target_dir(name))
        _restore_backup(backup_map.get(online.name), _get_target_dir(online.name))
        return {"success": False, "message": f"解压插件失败: {e}", "details": ""}
    except Exception as e:
        for name in installed_names:
            _restore_backup(backup_map.get(name), _get_target_dir(name))
        _restore_backup(backup_map.get(online.name), _get_target_dir(online.name))
        return {"success": False, "message": f"安装失败: {e}", "details": ""}

    # 安装 Python 依赖
    req_outputs: list[str] = []
    for name in installed_names + [online.name]:
        dep_online = next((d for d in deps_to_install if d.name == name), online)
        target = _get_target_dir(name, dep_online.directory)
        req_outputs.append(f"[{name}] {_install_requirements(target)}")

    # 清理备份
    for backup in backup_map.values():
        _cleanup_backup(backup)

    # 更新依赖关系
    db = SessionLocal()
    try:
        for dep in online.dependencies:
            dep_name = dep.get("name", "")
            if dep_name:
                update_dependent_by(db, dep_name, plugin_name, add=True)
    finally:
        db.close()

    # 同步数据库
    try:
        db = SessionLocal()
        try:
            sync_plugin_registry(db)
        finally:
            db.close()
    except Exception as e:
        logger.warning("同步注册表失败（插件已安装）: %s", e)

    dep_msg = ""
    if installed_names:
        dep_msg = f"（同时安装了依赖: {', '.join(installed_names)}）"

    return {
        "success": True,
        "message": f"插件 {online.display_name} ({plugin_name}) v{online.version} 安装成功{dep_msg}",
        "details": "\n".join(req_outputs),
        "dependencies_installed": installed_names,
    }


def update_plugin(plugin_name: str) -> dict:
    """更新在线插件（重新下载覆盖安装，含依赖检查）"""
    return install_plugin(plugin_name)


def _detect_plugin_from_zip(zf: zipfile.ZipFile) -> tuple[str, str, bool]:
    """从 zip 结构检测插件名和包名

    支持两种结构：
    A. {plugin_name}/{package_name}/...  (如 asmr_one/eta_asmr/plugin.py)
    B. {package_name}/...               (如 eta_asmr/plugin.py，无顶层目录)

    Returns:
        (plugin_name, package_name, is_library)
    """
    names = zf.namelist()
    if not names:
        raise ValueError("zip 包为空")

    # 收集顶层目录
    top_dirs: set[str] = set()
    for n in names:
        if "/" in n:
            top = n.split("/")[0]
            if top:
                top_dirs.add(top)

    if len(top_dirs) == 1:
        top = top_dirs.pop()
        # 检查 top 下是否有包目录（含 __init__.py）
        second_dirs: set[str] = set()
        for n in names:
            parts = n.split("/")
            if len(parts) >= 2 and parts[0] == top and parts[1]:
                second_dirs.add(parts[1])

        for pkg in sorted(second_dirs):
            if f"{top}/{pkg}/__init__.py" in names:
                has_plugin_py = f"{top}/{pkg}/plugin.py" in names
                # 检查是否是已知插件
                for pn, pkg_name in PLUGIN_PACKAGE_MAP.items():
                    if pkg_name == pkg:
                        return pn, pkg, not has_plugin_py
                # 未知插件，用顶层目录名作为插件名
                return top, pkg, not has_plugin_py

    # 结构 B：顶层就是包目录
    for pkg in sorted(top_dirs):
        if f"{pkg}/__init__.py" in names:
            has_plugin_py = f"{pkg}/plugin.py" in names
            for pn, pkg_name in PLUGIN_PACKAGE_MAP.items():
                if pkg_name == pkg:
                    return pn, pkg, not has_plugin_py
            # 未知包，用包名推导插件名
            return pkg.replace("eta_", "").replace("_", "").lower() or pkg, pkg, not has_plugin_py

    raise ValueError("无法从 zip 包中识别插件结构（未找到含 __init__.py 的包目录）")


def import_plugin_from_zip(zip_data: bytes) -> dict:
    """手动导入插件 zip 包

    流程：
    1. 计算 SHA256
    2. 校验 zip 路径（防穿越）
    3. 检测插件名和包名
    4. 如果匹配在线注册表且有 sha256，校验哈希
    5. 解压到临时目录，验证结构
    6. 移动到目标目录
    7. 安装 Python 依赖
    8. 检查并安装缺失依赖
    9. 同步注册表

    Returns:
        {success, message, details, plugin_name, dependencies_installed}
    """
    import tempfile

    from eta_web.plugins_manager.online import registry as online_registry
    from eta_web.plugins_manager.database import SessionLocal
    from eta_web.plugins_manager.manager import sync_plugin_registry, update_dependent_by

    # 1. 计算 SHA256
    actual_sha256 = _compute_sha256(zip_data)
    logger.info("导入插件 zip，SHA256: %s", actual_sha256)

    # 2-3. 校验 zip 并检测插件信息
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            _validate_zip_paths(zf)
            plugin_name, package_name, is_library = _detect_plugin_from_zip(zf)
            names = zf.namelist()
    except zipfile.BadZipFile as e:
        return {"success": False, "message": f"无效的 zip 文件: {e}", "details": ""}
    except ValueError as e:
        return {"success": False, "message": str(e), "details": ""}

    logger.info("检测到插件: %s (包名: %s, 库: %s)", plugin_name, package_name, is_library)

    # 4. SHA256 校验（如果在线注册表有声明）
    online = online_registry.get_plugin(plugin_name)
    if online and online.sha256:
        if actual_sha256 != online.sha256:
            return {
                "success": False,
                "message": f"SHA256 校验失败（期望 {online.sha256[:16]}...，实际 {actual_sha256[:16]}...）",
                "details": "",
                "plugin_name": plugin_name,
            }
        logger.info("SHA256 校验通过")
    elif online:
        logger.info("在线注册表未声明 SHA256，跳过校验")
    else:
        logger.info("未知插件（不在在线注册表中），跳过 SHA256 校验")

    # 5. 解压到临时目录
    target_dir = _get_target_dir(plugin_name)
    temp_dir: Optional[Path] = None
    backup: Optional[Path] = None

    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="plugin_import_"))
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            zf.extractall(temp_dir)

        # 确定实际解压后的插件目录
        # 如果是结构 A（{plugin_name}/...），实际目录是 temp_dir/{plugin_name}
        # 如果是结构 B（{package_name}/...），实际目录就是 temp_dir
        extracted_top = temp_dir / plugin_name
        if not extracted_top.exists():
            # 可能是结构 B，或者 plugin_name 是推导的
            # 检查 temp_dir 下是否有以 plugin_name 命名的目录
            # 如果没有，用 temp_dir 本身
            if (temp_dir / package_name / "__init__.py").exists():
                extracted_top = temp_dir
            else:
                # 尝试找到含 package_name 的顶层目录
                for child in temp_dir.iterdir():
                    if child.is_dir() and (child / package_name / "__init__.py").exists():
                        extracted_top = child
                        break
                else:
                    raise ValueError(f"解压后未找到包目录 {package_name}/")

        # 验证结构
        _validate_plugin_structure(extracted_top, package_name, is_library)

        # 6. 备份并移动到目标目录
        if target_dir.exists():
            backup = _backup_plugin(target_dir)

        # 复制到目标目录
        target_dir.mkdir(parents=True, exist_ok=True)
        for item in extracted_top.iterdir():
            dest = target_dir / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
            else:
                shutil.copy2(str(item), str(dest))

    except Exception as e:
        logger.error("导入插件失败: %s", e, exc_info=True)
        if backup:
            _restore_backup(backup, target_dir)
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
        return {
            "success": False,
            "message": f"导入失败: {e}",
            "details": "",
            "plugin_name": plugin_name,
        }

    # 清理临时目录
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir)

    # 7. 安装 Python 依赖
    req_output = _install_requirements(target_dir)

    # 注册路径
    add_plugin_path(plugin_name, target_dir, package_name)

    # 8. 检查并安装缺失依赖
    dependencies_installed: list[str] = []
    if online and online.dependencies:
        for dep in online.dependencies:
            dep_name = dep.get("name", "")
            dep_version = dep.get("version", "")
            if not dep_name:
                continue

            installed, compatible_dep, current_ver = _check_dependency_installed(dep_name, dep_version)

            if installed and compatible_dep:
                logger.info("依赖 %s 已安装且版本兼容，跳过", dep_name)
                db = SessionLocal()
                try:
                    update_dependent_by(db, dep_name, plugin_name, add=True)
                finally:
                    db.close()
                continue

            # 依赖未安装或不兼容，从在线注册表安装
            logger.info("依赖 %s 未安装或版本不兼容，从在线安装", dep_name)
            dep_result = install_plugin(dep_name)
            if dep_result.get("success"):
                dependencies_installed.append(dep_name)
                db = SessionLocal()
                try:
                    update_dependent_by(db, dep_name, plugin_name, add=True)
                finally:
                    db.close()
            else:
                logger.warning("自动安装依赖 %s 失败: %s", dep_name, dep_result.get("message"))
                # 依赖安装失败不阻止主插件导入，但警告用户
                req_output += f"\n[警告] 依赖 {dep_name} 安装失败: {dep_result.get('message')}"

    # 清理备份
    _cleanup_backup(backup)

    # 9. 同步数据库
    try:
        db = SessionLocal()
        try:
            sync_plugin_registry(db)
        finally:
            db.close()
    except Exception as e:
        logger.warning("同步注册表失败（插件已导入）: %s", e)

    dep_msg = ""
    if dependencies_installed:
        dep_msg = f"（同时安装了依赖: {', '.join(dependencies_installed)}）"

    return {
        "success": True,
        "message": f"插件 {plugin_name} 导入成功{dep_msg}",
        "details": req_output,
        "plugin_name": plugin_name,
        "dependencies_installed": dependencies_installed,
    }
