"""元数据批量编辑、重命名预览/执行（admin）"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import require_admin
from app.plugins.local_node.metadata_editor import (
    EDITABLE_FIELDS,
    batch_preview,
    batch_update_field,
    batch_update_multi_fields,
    rename_execute,
    rename_preview,
)
from app.plugins.local_node.models import Track, User
from app.plugins.local_node.schemas import (
    FieldOverview,
    MetadataBatchUpdateRequest,
    MetadataBatchUpdateResult,
    MetadataPreview,
    MetadataPreviewRequest,
    MetadataUpdateFieldRequest,
    RenamePreview,
    RenameRequest,
    RenameResult,
)
from app.utils.tag_writer import (
    AUDIO_EXTS,
    write_cover_to_file,
    write_lyrics_to_file,
)


logger = logging.getLogger("etamusic.local_node.metadata")
router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.post("/preview", response_model=MetadataPreview)
def preview_metadata(
    payload: MetadataPreviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> MetadataPreview:
    """看板：返回各字段公共值或差异标记"""
    overview = batch_preview(db, payload.track_ids)
    fields = {
        k: FieldOverview(value=v["value"], is_uniform=v["is_uniform"])
        for k, v in overview.items()
    }
    return MetadataPreview(track_ids=payload.track_ids, fields=fields)


@router.post("/update-field", response_model=dict)
def update_field(
    payload: MetadataUpdateFieldRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """批量改单字段（行内双击编辑用）"""
    if payload.field not in EDITABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的字段: {payload.field}，可选: {list(EDITABLE_FIELDS.keys())}",
        )
    count = batch_update_field(db, payload.track_ids, payload.field, payload.value)
    return {"updated": count}


@router.post("/batch-update", response_model=MetadataBatchUpdateResult)
def batch_update(
    payload: MetadataBatchUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> MetadataBatchUpdateResult:
    """多字段批量保存（右侧边栏一次保存多个字段用）

    所有 track_ids 都会被写入 updates 里的全部字段值。
    updates 里 None 或空串表示清空该字段。
    """
    if not payload.track_ids:
        raise HTTPException(status_code=400, detail="track_ids 不能为空")
    if not payload.updates:
        raise HTTPException(status_code=400, detail="updates 不能为空")
    result = batch_update_multi_fields(db, payload.track_ids, payload.updates)
    return MetadataBatchUpdateResult(**result)


@router.post("/rename-preview", response_model=RenamePreview)
def preview_rename(
    payload: RenameRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> RenamePreview:
    """重命名预览"""
    if not payload.template:
        raise HTTPException(status_code=400, detail="模板不能为空")
    items = rename_preview(db, payload.track_ids, payload.template, payload.exceptions)
    from app.plugins.local_node.schemas import RenamePreviewItem

    return RenamePreview(
        items=[
            RenamePreviewItem(track_id=it["track_id"], old_path=it["old_path"], new_path=it["new_path"])
            for it in items
        ]
    )


@router.post("/rename-execute", response_model=RenameResult)
def execute_rename(
    payload: RenameRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> RenameResult:
    """执行重命名（事务保护，失败回滚）"""
    if not payload.template:
        raise HTTPException(status_code=400, detail="模板不能为空")
    result = rename_execute(db, payload.track_ids, payload.template, payload.exceptions)
    return RenameResult(success=result["success"], failed=result["failed"])


# ===== 歌词批量写入 =====


@router.post("/batch-lyrics")
def batch_write_lyrics(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """批量把歌词写入多首曲目的文件 USLT/©lyr tag 并更新 DB 标志位

    请求体: { "track_ids": [int], "lyrics": str }
    """
    track_ids = payload.get("track_ids") or []
    lyrics = payload.get("lyrics") or ""
    if not isinstance(track_ids, list) or not track_ids:
        raise HTTPException(status_code=400, detail="track_ids 不能为空")

    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    success = 0
    failed: list[dict] = []
    for t in tracks:
        try:
            ok = write_lyrics_to_file(t.abs_path, lyrics)
            if ok:
                t.lyrics_embedded = True
                success += 1
            else:
                failed.append({"track_id": t.id, "title": t.title, "reason": "写入失败（可能是不支持的格式）"})
        except Exception as e:
            failed.append({"track_id": t.id, "title": t.title, "reason": str(e)})
    db.commit()
    return {
        "updated": success,
        "failed": failed,
        "lyrics_preview": lyrics[:200] if lyrics else "",
    }


# ===== 封面批量管理 =====


def _detect_image_mime(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


@router.post("/batch-cover")
async def batch_upload_cover(
    track_ids: str = Form(..., description="逗号分隔的 track_id 列表"),
    file: UploadFile = File(..., description="封面图片文件"),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """批量把同一张封面嵌入到多首曲目

    track_ids 以 form 字段传入（逗号分隔），因为 multipart 不能同时接收 list 和 file。
    """
    try:
        ids = [int(x.strip()) for x in track_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="track_ids 必须是逗号分隔的整数列表")
    if not ids:
        raise HTTPException(status_code=400, detail="track_ids 不能为空")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")
    mime = _detect_image_mime(content)

    tracks = db.query(Track).filter(Track.id.in_(ids)).all()
    success = 0
    failed: list[dict] = []
    for t in tracks:
        try:
            ok = write_cover_to_file(t.abs_path, content, mime)
            if ok:
                t.cover_embedded = True
                success += 1
            else:
                failed.append({"track_id": t.id, "title": t.title, "reason": "写入失败"})
        except Exception as e:
            failed.append({"track_id": t.id, "title": t.title, "reason": str(e)})
    db.commit()
    return {"updated": success, "failed": failed, "mime": mime, "size": len(content)}


@router.post("/batch-cover-remove")
def batch_remove_cover(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """批量删除多首曲目文件内嵌的封面

    请求体: { "track_ids": [int] }
    """
    track_ids = payload.get("track_ids") or []
    if not isinstance(track_ids, list) or not track_ids:
        raise HTTPException(status_code=400, detail="track_ids 不能为空")

    from mutagen import File as MutagenFile
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4

    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    success = 0
    failed: list[dict] = []
    for t in tracks:
        mf = None
        try:
            mf = MutagenFile(t.abs_path)
            if mf is None:
                failed.append({"track_id": t.id, "title": t.title, "reason": "无法打开文件"})
                continue
            if isinstance(mf, FLAC):
                mf.clear_pictures()
                mf.save()
            elif isinstance(mf, MP4):
                if mf.tags and "covr" in mf.tags:
                    del mf.tags["covr"]
                    mf.save()
            else:
                # MP3 / WAVE ID3 APIC
                tags = getattr(mf, "tags", None)
                if tags is not None:
                    for k in list(tags.keys()):
                        if k.startswith("APIC"):
                            del tags[k]
                    mf.save()
            t.cover_embedded = False
            success += 1
        except Exception as e:
            failed.append({"track_id": t.id, "title": t.title, "reason": str(e)})
        finally:
            if mf is not None:
                try:
                    mf.close()
                except Exception:
                    pass
    db.commit()
    return {"updated": success, "failed": failed}



