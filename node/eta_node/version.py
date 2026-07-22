"""EtaMusic Node 版本与功能能力定义

所有版本号、API 协议版本、功能清单的单一来源。
客户端通过 GET /api/version 读取此信息进行兼容性校验。
"""
from __future__ import annotations

# node 软件版本号（语义化版本）
# - 主版本：API 协议不兼容变更
# - 次版本：向后兼容的新功能
# - 修订号：bug 修复
# 1.2.0: 新增数据版本号 data_versions，tracks/playlists 表加 deleted_at 软删除，
#        暴露 /api/{entity}/changes 增量接口，供访问端离线缓存同步
# 1.2.1: 曲目删除与库一致性——新增 track_delete 任务（补偿事务 + 软删除）、
#        真 SHA-256 file_hash（替代伪实现）、播放列表权限 view/edit 拆分、
#        所有读取路径补齐软删除过滤、扫描器缺失文件清理与软删除恢复
# 1.2.2: standalone 启动前端口冲突检测——被 eta_node 自身占用自动杀掉重启，
#        被其他程序占用报错退出（新增 eta_node.port_manager 模块）
# 1.2.3: 新增播放完成判定配置——区分音乐/广播剧，按曲目时长应用不同完成百分比，
#        GET/PUT /api/settings/playback；新增 PlaybackSettings 表（单行，id=1）
# 1.3.0: 播放列表文件夹——新增 PlaylistFolder 自引用树形模型 + /api/playlist-folders CRUD，
#        Playlist 加 folder_id 外键，m3u 文件夹导入保留相对目录层级（自动创建同名文件夹）
NODE_VERSION = "1.3.0"

# API 协议主版本
# 当客户端的 CLIENT_API_VERSION 与此值不一致时，视为完全不兼容，
# 拒绝连接并提示升级。
API_VERSION = 1

# 该 node 要求的最小客户端版本
# 低于此版本的客户端将被拒绝连接
MIN_CLIENT_VERSION = "1.2.0"

# node 支持的功能清单
# 客户端据此判断哪些功能可用、哪些被禁用
# 新增功能时往此列表追加，不要删除已有项（除非确实移除了该路由）
NODE_FEATURES = [
    "auth",           # 认证（login/refresh/me）
    "tracks",         # 曲目浏览/流式播放/封面/歌词
    "playlists",      # 播放列表 CRUD
    "watch_dirs",     # 监控目录管理
    "scan",           # 扫描入库
    "upload",         # 文件上传/暂存
    "metadata",       # 元数据批量编辑
    "dedup",          # 去重检测
    "quality",        # 音质升级
    "users",          # 用户管理
    "permissions",    # 播放列表授权
    "tasks",          # 任务队列
    "audit",          # 审计日志
    "stats",          # 播放统计/数据看板
    "inbox",          # 收集箱
    "import_m3u",     # m3u 播放列表导入
    "data_sync",      # 数据版本号 + 增量同步接口（/api/{entity}/changes）
]


def get_version_info(data_versions: dict[str, int] | None = None) -> dict:
    """返回版本信息字典（供 /api/version 端点使用）

    Args:
        data_versions: 数据版本号字典 {tracks: N, playlists: N}，由路由层从 DB 读取后传入。
                       None 时不包含该字段（向后兼容旧调用方，但 /api/version 路由总会传入）。
    """
    info = {
        "version": NODE_VERSION,
        "api_version": API_VERSION,
        "min_client_version": MIN_CLIENT_VERSION,
        "features": list(NODE_FEATURES),
    }
    if data_versions is not None:
        info["data_versions"] = data_versions
    return info
