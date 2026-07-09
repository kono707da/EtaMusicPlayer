"""FastAPI 依赖：数据库会话、当前用户、管理员校验、流式 token 校验"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.models import User
from eta_node.security import decode_token


def _resolve_user(token: str, db: Session) -> User:
    """解析 token 并返回用户对象"""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_raw = payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="token 主体非法")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user


def get_current_user_dependency(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """标准依赖：从 Authorization 头解析用户"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或无效的认证头",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    return _resolve_user(token, db)


def get_user_from_query_token(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
) -> User:
    """流式接口专用：从 query 参数 ?token= 解析用户"""
    return _resolve_user(token, db)


def require_admin(user: User = Depends(get_current_user_dependency)) -> User:
    """要求当前用户为管理员"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
