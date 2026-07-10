"""扫描触发与状态查询（admin）

扫描现在通过任务队列异步执行：
- POST /api/scan 提交 scan 类型的 NodeTask，返回 task_id
- GET /api/scan/{task_id} 查询扫描状态（兼容旧 ScanTask 和新 NodeTask）
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import require_admin
from eta_node.models import NodeTask, ScanTask, User
from eta_node.schemas import NodeTaskOut, ScanRequest, ScanTaskOut

logger = logging.getLogger("eta_node.routers.scan")

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("", response_model=NodeTaskOut, status_code=201)
def trigger_scan(
    payload: ScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> NodeTaskOut:
    """触发扫描（异步任务），返回 task_id

    扫描通过任务队列串行执行，避免并发写入冲突。
    客户端通过 GET /api/tasks/{task_id} 或 GET /api/scan/{task_id} 轮询状态。
    """
    task_payload = {"watch_dir_id": payload.watch_dir_id}
    task = NodeTask(
        task_type="scan",
        status="pending",
        priority=-10,  # 后台任务，低优先级
        payload=task_payload,
        submitted_by=user.username,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    logger.info("用户 %s 提交扫描任务 #%d (watch_dir_id=%s)",
                user.username, task.id, payload.watch_dir_id)
    return NodeTaskOut.model_validate(task)


@router.get("/{task_id}")
def get_scan_status(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """查询扫描状态（兼容旧 ScanTask 和新 NodeTask）"""
    # 先查 NodeTask
    node_task = db.get(NodeTask, task_id)
    if node_task is not None:
        result = node_task.result or {}
        return {
            "id": node_task.id,
            "task_type": "scan",
            "status": node_task.status,
            "progress": node_task.progress,
            "total_files": result.get("total_files", 0),
            "new_tracks": result.get("new_tracks", 0),
            "updated_tracks": result.get("updated_tracks", 0),
            "error_message": node_task.error_message,
            "started_at": node_task.started_at,
            "finished_at": node_task.finished_at,
            "submitted_at": node_task.submitted_at,
            "submitted_by": node_task.submitted_by,
        }

    # 向后兼容：查旧的 ScanTask
    scan_task = db.get(ScanTask, task_id)
    if scan_task is not None:
        return ScanTaskOut.model_validate(scan_task).model_dump()

    raise HTTPException(status_code=404, detail="扫描任务不存在")
