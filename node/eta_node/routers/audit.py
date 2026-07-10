"""审计日志查询 API（admin）

记录何时哪个访问端用哪个用户做了什么重要操作。
审计日志由任务处理器在执行写操作时自动写入。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import require_admin
from eta_node.models import AuditLog, User

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    username: Optional[str] = None
    client_ip: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[dict] = None
    task_id: Optional[int] = None

    model_config = {"from_attributes": True}


class AuditLogList(BaseModel):
    total: int
    page: int
    size: int
    items: list[AuditLogOut]


@router.get("/logs", response_model=AuditLogList)
def list_audit_logs(
    action: Optional[str] = Query(default=None, description="按操作类型过滤"),
    username: Optional[str] = Query(default=None, description="按用户名过滤"),
    target_type: Optional[str] = Query(default=None, description="按目标类型过滤"),
    start_date: Optional[datetime] = Query(default=None, description="开始时间"),
    end_date: Optional[datetime] = Query(default=None, description="结束时间"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> AuditLogList:
    """查询审计日志（分页，按时间倒序）"""
    query = db.query(AuditLog)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if username is not None:
        query = query.filter(AuditLog.username == username)
    if target_type is not None:
        query = query.filter(AuditLog.target_type == target_type)
    if start_date is not None:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date is not None:
        query = query.filter(AuditLog.timestamp <= end_date)

    total = query.count()
    items = (
        query.order_by(AuditLog.timestamp.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return AuditLogList(
        total=total,
        page=page,
        size=size,
        items=[AuditLogOut.model_validate(log) for log in items],
    )
