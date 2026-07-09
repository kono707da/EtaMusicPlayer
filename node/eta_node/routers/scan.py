"""扫描触发与状态查询（admin）"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from eta_node.database import SessionLocal, get_db
from eta_node.deps import require_admin
from eta_node.models import ScanTask, User
from eta_node.schemas import ScanRequest, ScanTaskOut
from eta_node.scanner import run_scan


router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("", response_model=ScanTaskOut, status_code=201)
def trigger_scan(
    payload: ScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> ScanTaskOut:
    """触发扫描，返回 scan_task_id。同步执行（后续可改后台任务）"""
    task = ScanTask(status="pending", started_at=datetime.utcnow())
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id
    # 释放当前请求 session 后再执行扫描（扫描内部使用独立 session）
    db.close()

    run_scan(task_id, watch_dir_id=payload.watch_dir_id)

    db2 = SessionLocal()
    try:
        refreshed = db2.get(ScanTask, task_id)
        return ScanTaskOut.model_validate(refreshed)
    finally:
        db2.close()


@router.get("/{task_id}", response_model=ScanTaskOut)
def get_scan_status(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> ScanTaskOut:
    """查询扫描状态"""
    task = db.get(ScanTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="扫描任务不存在")
    return ScanTaskOut.model_validate(task)
