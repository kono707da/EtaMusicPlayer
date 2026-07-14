"""系统信息路由：版本与功能能力

GET /api/version 无需认证，供客户端在登录前进行版本兼容性校验。
"""
from __future__ import annotations

from fastapi import APIRouter

from eta_node.version import get_version_info

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/version")
def get_version() -> dict:
    """返回 node 版本号、API 协议版本、支持的功能清单

    客户端据此判断：
    - API 协议不兼容 → 拒绝连接
    - node 版本低于客户端要求 → 拒绝连接
    - 部分功能缺失 → 允许连接但禁用对应 UI
    """
    return get_version_info()
