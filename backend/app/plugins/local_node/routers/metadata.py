"""元数据批量编辑、重命名预览/执行（admin）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.plugins.local_node.database import get_db
from app.plugins.local_node.deps import require_admin
from app.plugins.local_node.metadata_editor import (
    EDITABLE_FIELDS,
    batch_preview,
    batch_update_field,
    rename_execute,
    rename_preview,
)
from app.plugins.local_node.models import User
from app.plugins.local_node.schemas import (
    FieldOverview,
    MetadataPreview,
    MetadataPreviewRequest,
    MetadataUpdateFieldRequest,
    RenamePreview,
    RenameRequest,
    RenameResult,
)


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
    """批量改单字段"""
    if payload.field not in EDITABLE_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的字段: {payload.field}，可选: {list(EDITABLE_FIELDS.keys())}",
        )
    count = batch_update_field(db, payload.track_ids, payload.field, payload.value)
    return {"updated": count}


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
