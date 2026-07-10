"""文件上传到 watch_dir（admin）—供远程下载推送使用

访问端下载资源到本地缓存池后，通过此接口将文件推送到远程节点。

两种上传模式：
1. 直接上传（旧）：POST /api/upload — 文件直接写入 watch_dir（同步）
2. 暂存 + 任务（新）：POST /api/upload/stage → POST /api/tasks — 文件先暂存，通过任务队列移动入库
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from eta_node.config import settings
from eta_node.database import get_db
from eta_node.deps import require_admin
from eta_node.models import User, WatchDir

router = APIRouter(prefix="/api/upload", tags=["upload"])

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def _sanitize(name: str) -> str:
    return _INVALID_CHARS.sub("_", name).strip().rstrip(".")


def _build_target(
    watch_dir_path: str,
    subdir: str,
    work_title: str,
    file_rel_path: str,
) -> Path:
    parts = [watch_dir_path]
    if subdir:
        parts.append(subdir.strip("/\\"))
    parts.append(_sanitize(work_title))
    for seg in file_rel_path.split("/"):
        if seg:
            parts.append(_sanitize(seg))
    return Path(*parts)


@router.post("")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    watch_dir_id: int = Form(...),
    subdir: str = Form(default=""),
    work_title: str = Form(...),
    file_rel_path: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """上传单个文件到指定 watch_dir 的子目录

    文件最终路径：{watch_dir_path}/{subdir}/{work_title}/{file_rel_path}
    使用 .part 临时文件 + os.replace 原子写入。
    """
    wd = db.get(WatchDir, watch_dir_id)
    if wd is None:
        raise HTTPException(status_code=404, detail="监控目录不存在")

    target = _build_target(wd.path, subdir, work_title, file_rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    tmp = target.with_suffix(target.suffix + ".part")
    total = 0
    try:
        with open(tmp, "wb") as f:
            while True:
                chunk = await file.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        tmp.replace(target)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"写入文件失败: {e}")

    return {
        "saved_to": str(target),
        "size": total,
    }


@router.post("/check")
def check_file_exists(
    watch_dir_id: int = Form(...),
    subdir: str = Form(default=""),
    work_title: str = Form(...),
    file_rel_path: str = Form(...),
    expected_size: int = Form(default=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """检查文件是否已存在于节点上（用于断点续传/秒传判断）"""
    wd = db.get(WatchDir, watch_dir_id)
    if wd is None:
        raise HTTPException(status_code=404, detail="监控目录不存在")

    target = _build_target(wd.path, subdir, work_title, file_rel_path)
    if target.exists() and expected_size > 0 and target.stat().st_size == expected_size:
        return {"exists": True, "size": target.stat().st_size, "saved_to": str(target)}
    return {"exists": False, "size": 0, "saved_to": None}


@router.post("/stage")
async def stage_file(
    file: UploadFile = File(..., description="要暂存的文件"),
    user: User = Depends(require_admin),
) -> dict:
    """暂存文件到临时目录，返回 staging_path

    上传流程：
    1. POST /api/upload/stage — 暂存文件，得到 staging_path
    2. POST /api/tasks — 提交 upload 任务，payload 包含 staging_path + 目标路径参数
    3. GET /api/tasks/{task_id} — 轮询任务状态

    文件在暂存目录中保存为 {uuid}.{原始扩展名}，任务执行时移动到 watch_dir。
    """
    staging_dir = settings.staging_absolute_path
    staging_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ""
    staging_name = f"{uuid.uuid4().hex}{ext}"
    staging_path = staging_dir / staging_name

    total = 0
    try:
        with open(staging_path, "wb") as f:
            while True:
                chunk = await file.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
    except Exception as e:
        staging_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"暂存文件写入失败: {e}")

    return {
        "staging_path": str(staging_path),
        "filename": file.filename,
        "size": total,
    }

