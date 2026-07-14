"""EtaMusic Node 版本与功能能力定义

所有版本号、API 协议版本、功能清单的单一来源。
客户端通过 GET /api/version 读取此信息进行兼容性校验。
"""
from __future__ import annotations

# node 软件版本号（语义化版本）
# - 主版本：API 协议不兼容变更
# - 次版本：向后兼容的新功能
# - 修订号：bug 修复
NODE_VERSION = "1.1.0"

# API 协议主版本
# 当客户端的 CLIENT_API_VERSION 与此值不一致时，视为完全不兼容，
# 拒绝连接并提示升级。
API_VERSION = 1

# 该 node 要求的最小客户端版本
# 低于此版本的客户端将被拒绝连接
MIN_CLIENT_VERSION = "1.1.0"

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
]


def get_version_info() -> dict:
    """返回版本信息字典（供 /api/version 端点使用）"""
    return {
        "version": NODE_VERSION,
        "api_version": API_VERSION,
        "min_client_version": MIN_CLIENT_VERSION,
        "features": list(NODE_FEATURES),
    }
