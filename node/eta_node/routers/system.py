"""系统信息路由：版本与功能能力

GET /api/version 无需认证，供客户端在登录前进行版本兼容性校验。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.version import get_version_info
from eta_node.versioning import get_all_versions

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/version")
def get_version(db: Session = Depends(get_db)) -> dict:
    """返回 node 版本号、API 协议版本、支持的功能清单、数据版本号

    客户端据此判断：
    - API 协议不兼容 → 拒绝连接
    - node 版本低于客户端要求 → 拒绝连接
    - 部分功能缺失 → 允许连接但禁用对应 UI
    - data_versions 与本地 last_sync_version 比对 → 决定是否拉取增量
    """
    return get_version_info(data_versions=get_all_versions(db))
