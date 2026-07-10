"""单线程任务执行器

节点自治核心：所有写操作通过任务队列串行执行。
访问端只提交任务请求，节点自主调度执行，避免并发数据库写入冲突。

用法:
    executor = TaskExecutor()
    executor.register_handler("scan", _handle_scan)
    executor.start()        # 启动后台守护线程
    executor.stop()         # 停止（应用关闭时调用）
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy.orm import Session

from eta_node.database import SessionLocal
from eta_node.models import AuditLog, NodeTask

logger = logging.getLogger("eta_node.task_executor")

# 任务处理器签名: (db, payload, task) -> result_dict | None
TaskHandler = Callable[[Session, Optional[dict], NodeTask], Optional[dict]]


class TaskExecutor:
    """单线程任务执行器

    从数据库 node_tasks 表中按优先级 + 提交时间顺序取出 pending 任务，
    串行执行。保证同一时刻只有一个任务在写数据库。
    """

    def __init__(self, poll_interval: float = 1.0) -> None:
        self._poll_interval = poll_interval
        self._handlers: dict[str, TaskHandler] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ---- 处理器注册 ----

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        """注册任务处理器"""
        self._handlers[task_type] = handler
        logger.debug("已注册任务处理器: %s", task_type)

    # ---- 生命周期 ----

    def start(self) -> None:
        """启动后台守护线程"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("任务执行器已在运行")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="task-executor", daemon=True
        )
        self._thread.start()
        logger.info("任务执行器已启动 (poll_interval=%.1fs)", self._poll_interval)

    def stop(self, timeout: float = 5.0) -> None:
        """停止后台线程"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        logger.info("任务执行器已停止")

    # ---- 内部逻辑 ----

    def _run_loop(self) -> None:
        """主循环：不断拉取并执行 pending 任务"""
        while not self._stop_event.is_set():
            try:
                processed = self._pick_and_execute()
                if not processed:
                    # 没有任务，等待
                    self._stop_event.wait(self._poll_interval)
            except Exception:
                logger.exception("任务执行器主循环异常")
                self._stop_event.wait(self._poll_interval)

    def _pick_and_execute(self) -> bool:
        """取出一个 pending 任务并执行，返回是否处理了任务"""
        task_id: Optional[int] = None
        db = SessionLocal()
        try:
            # 按优先级降序 + 提交时间升序取一个 pending 任务
            task = (
                db.query(NodeTask)
                .filter(NodeTask.status == "pending")
                .order_by(NodeTask.priority.desc(), NodeTask.submitted_at.asc())
                .with_for_update(skip_locked=True)
                .first()
            )
            if task is None:
                return False

            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()
            task_id = task.id
            task_type = task.task_type
            payload = task.payload
            db.close()

            # 在独立 session 中执行任务
            result = self._execute_task(task_id, task_type, payload)

            # 更新结果
            db2 = SessionLocal()
            try:
                task = db2.get(NodeTask, task_id)
                if task is not None:
                    task.status = "completed"
                    task.result = result
                    task.progress = 100
                    task.finished_at = datetime.utcnow()
                    db2.commit()
            finally:
                db2.close()

            logger.info("任务 #%d (%s) 完成", task_id, task_type)
            return True

        except Exception as e:
            logger.exception("任务执行失败 (task_id=%s)", task_id)
            # 标记失败
            if task_id is not None:
                try:
                    db2 = SessionLocal()
                    try:
                        task = db2.get(NodeTask, task_id)
                        if task is not None:
                            task.status = "failed"
                            task.error_message = str(e)[:4000]
                            task.finished_at = datetime.utcnow()
                            db2.commit()
                    finally:
                        db2.close()
                except Exception:
                    logger.exception("标记任务失败状态时也出错")
            return True  # 消费了一个任务（虽然失败了）
        finally:
            db.close()

    def _execute_task(
        self, task_id: int, task_type: str, payload: Optional[dict]
    ) -> Optional[dict]:
        """执行单个任务（在独立 session 中）"""
        handler = self._handlers.get(task_type)
        if handler is None:
            raise ValueError(f"未注册的任务类型: {task_type}")

        db = SessionLocal()
        try:
            task = db.get(NodeTask, task_id)
            if task is None:
                raise ValueError(f"任务不存在: {task_id}")

            result = handler(db, payload, task)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


# ---- 全局单例 ----

_executor: Optional[TaskExecutor] = None


def get_executor() -> TaskExecutor:
    """获取全局 TaskExecutor 实例"""
    global _executor
    if _executor is None:
        _executor = TaskExecutor()
    return _executor


def start_executor() -> None:
    """启动任务执行器并注册所有内置处理器"""
    from eta_node.task_handlers import register_all_handlers

    executor = get_executor()
    register_all_handlers(executor)
    executor.start()


def stop_executor() -> None:
    """停止任务执行器"""
    global _executor
    if _executor is not None:
        _executor.stop()
        _executor = None


# ---- 审计日志辅助 ----

def write_audit_log(
    db: Session,
    *,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    client_ip: Optional[str] = None,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    detail: Optional[dict] = None,
    task_id: Optional[int] = None,
) -> None:
    """写入审计日志（不自动 commit，由调用方控制事务）"""
    log = AuditLog(
        user_id=user_id,
        username=username,
        client_ip=client_ip,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        task_id=task_id,
    )
    db.add(log)
