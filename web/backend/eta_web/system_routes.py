"""系统级 API 路由

提供日志查看等运维辅助能力，挂在 /api/system 下。
不依赖任何插件，供设置页面的系统设置使用。
"""
from __future__ import annotations

import logging
import re
from collections import deque
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("eta_web.system")

router = APIRouter(prefix="/api/system", tags=["system"])


class FrontendErrorReport(BaseModel):
    """前端错误上报请求体"""

    title: str = Field(..., description="错误标题")
    description: str = Field("", description="错误详情")
    url: str = Field("", description="触发错误的页面 URL")
    timestamp: str = Field("", description="前端时间戳")

# 日志文件路径（与 main.py 中 LOG_FILE 保持一致）
_BACKEND_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = _BACKEND_DIR / "data" / "logs" / "eta_web.log"

# 级别权重，用于 >= 过滤
_LEVEL_WEIGHT: dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# 匹配日志行中的级别字段：`%(asctime)s [%(levelname)s] %(name)s: %(message)s`
_LINE_LEVEL_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*\s*\[(\w+)\]")


def _read_tail_lines(path: Path, max_lines: int) -> list[str]:
    """从文件读取最后 max_lines 行（保留原始顺序）。

    日志文件由 TimedRotatingFileHandler 管理，按天轮转保留 30 天。
    当前活跃文件即 eta_web.log，全量读取开销可控。
    使用 deque(maxlen=max_lines) 自动保留尾部，避免一次性加载全部到列表。
    """
    if not path.exists():
        return []
    try:
        buf: deque[str] = deque(maxlen=max_lines)
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                buf.append(line.rstrip("\r\n"))
        return list(buf)
    except OSError as exc:
        logger.warning("读取日志文件失败: %s", exc, exc_info=True)
        return []


@router.post("/frontend-error")
def report_frontend_error(report: FrontendErrorReport) -> dict:
    """接收前端错误上报，写入后端日志。

    前端 toast.error 触发时会异步调用此端点（fire-and-forget），
    使前端 UI 错误也能在设置页面的日志查看中检索到。
    """
    logger.error(
        "前端错误: [%s] %s | URL: %s | 时间: %s",
        report.title,
        report.description,
        report.url,
        report.timestamp,
    )
    return {"ok": True}


@router.get("/logs")
def get_logs(
    lines: int = Query(500, ge=1, le=5000, description="返回最近 N 行日志"),
    level: str = Query(
        "ALL",
        description="级别过滤：ALL/DEBUG/INFO/WARNING/ERROR/CRITICAL（含更高级别）",
    ),
) -> dict:
    """读取最近 N 行日志，支持按级别过滤。

    日志文件位于 web/backend/data/logs/eta_web.log（TimedRotatingFileHandler，按天轮转保留 30 天）。
    前端用于排查错误时获取后端运行日志。
    """
    level_upper = (level or "ALL").upper()
    if level_upper != "ALL" and level_upper not in _LEVEL_WEIGHT:
        raise HTTPException(
            status_code=400,
            detail=f"无效的日志级别: {level}，可选: ALL/DEBUG/INFO/WARNING/ERROR/CRITICAL",
        )

    raw_lines = _read_tail_lines(LOG_FILE, lines)

    if level_upper == "ALL":
        filtered = raw_lines
    else:
        threshold = _LEVEL_WEIGHT[level_upper]
        filtered = []
        last_passed = False  # 上一行是否通过了过滤（用于多行 traceback 续行）
        for ln in raw_lines:
            m = _LINE_LEVEL_RE.match(ln)
            if m:
                lv = m.group(1).upper()
                last_passed = _LEVEL_WEIGHT.get(lv, 0) >= threshold
                if last_passed:
                    filtered.append(ln)
            else:
                # 无级别标记的行（多行 traceback 续行），跟随上一行级别判定
                if last_passed:
                    filtered.append(ln)

    file_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0

    return {
        "lines": filtered,
        "total_returned": len(filtered),
        "requested_lines": lines,
        "level": level_upper,
        "file_path": str(LOG_FILE),
        "file_size": file_size,
        "exists": LOG_FILE.exists(),
    }
