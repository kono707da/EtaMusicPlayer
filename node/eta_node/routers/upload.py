"""文件上传到 watch_dir（admin）—供远程下载推送使用

访问端下载资源到本地缓存池后，通过此接口将文件推送到远程节点。
"""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

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
