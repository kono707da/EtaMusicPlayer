"""收集箱路由：按路径查找曲目、添加曲目到收集箱（admin）"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from eta_node.database import get_db
from eta_node.deps import require_admin
from eta_node.inbox import add_tracks_to_inbox, find_tracks_by_paths
from eta_node.models import User

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


class ByPathsRequest(BaseModel):
    paths: list[str]


class ByPathsResponse(BaseModel):
    track_ids: list[int]


class AddToInboxRequest(BaseModel):
    track_ids: list[int]


class AddToInboxResponse(BaseModel):
    added: int


@router.post("/by-paths", response_model=ByPathsResponse)
def find_tracks(
    payload: ByPathsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> ByPathsResponse:
    """根据文件绝对路径列表查找曲目 ID（admin）"""
    track_ids = find_tracks_by_paths(payload.paths)
    return ByPathsResponse(track_ids=track_ids)


@router.post("/add", response_model=AddToInboxResponse)
def add_to_inbox(
    payload: AddToInboxRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> AddToInboxResponse:
    """将曲目添加到收集箱（admin）"""
    added = add_tracks_to_inbox(payload.track_ids)
    return AddToInboxResponse(added=added)
