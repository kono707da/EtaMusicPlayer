"""任务队列 API：提交、查询、取消任务

所有写操作通过任务队列串行执行。访问端提交任务后返回 task_id，
通过 GET /api/tasks/{task_id} 轮询任务状态。
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import require_admin
from eta_node.models import NodeTask, User
from eta_node.schemas import NodeTaskList, NodeTaskOut, TaskSubmitRequest

logger = logging.getLogger("eta_node.routers.tasks")

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 允许提交的任务类型
_ALLOWED_TASK_TYPES = {
    "scan",
    "upload",
    "playlist_add",
    "playlist_remove",
    "playlist_reorder",
    "metadata_update",
    "metadata_rename",
    "watch_dir_create",
    "watch_dir_update",
    "watch_dir_delete",
    "user_create",
    "user_update",
    "user_delete",
    "permission_grant",
    "permission_revoke",
    "dedup_update",
}


@router.post("", response_model=NodeTaskOut, status_code=201)
def submit_task(
    payload: TaskSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> NodeTaskOut:
    """提交一个新任务到队列"""
    if payload.task_type not in _ALLOWED_TASK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的任务类型: {payload.task_type}，"
                   f"允许: {', '.join(sorted(_ALLOWED_TASK_TYPES))}",
        )

    task = NodeTask(
        task_type=payload.task_type,
        status="pending",
        priority=payload.priority,
        payload=payload.payload,
        submitted_by=user.username,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    logger.info(
        "用户 %s 提交任务 #%d (%s, priority=%d)",
        user.username, task.id, task.task_type, task.priority,
    )
    return NodeTaskOut.model_validate(task)


@router.get("/{task_id}", response_model=NodeTaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> NodeTaskOut:
    """查询单个任务状态"""
    task = db.get(NodeTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return NodeTaskOut.model_validate(task)


@router.get("", response_model=NodeTaskList)
def list_tasks(
    status: Optional[str] = Query(default=None, description="按状态过滤"),
    task_type: Optional[str] = Query(default=None, description="按类型过滤"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> NodeTaskList:
    """列出任务（分页，按提交时间倒序）"""
    query = db.query(NodeTask)
    if status is not None:
        query = query.filter(NodeTask.status == status)
    if task_type is not None:
        query = query.filter(NodeTask.task_type == task_type)

    total = query.count()
    items = (
        query.order_by(NodeTask.submitted_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return NodeTaskList(
        total=total,
        page=page,
        size=size,
        items=[NodeTaskOut.model_validate(t) for t in items],
    )


@router.post("/{task_id}/cancel", response_model=NodeTaskOut)
def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> NodeTaskOut:
    """取消一个 pending 任务（running 任务不可取消）"""
    task = db.get(NodeTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"任务状态为 {task.status}，只有 pending 任务可取消",
        )
    task.status = "cancelled"
    task.finished_at = __import__("datetime").datetime.utcnow()
    db.commit()
    db.refresh(task)
    logger.info("用户 %s 取消任务 #%d", user.username, task_id)
    return NodeTaskOut.model_validate(task)
