"""Pydantic 请求/响应模型"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ----------------------------- Auth -----------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------------- Tracks -----------------------------
class TrackOut(BaseModel):
    id: int
    watch_dir_id: int
    rel_path: str
    filename: str
    ext: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    track_no: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_size: Optional[int] = None
    cover_embedded: bool = False
    lyrics_embedded: bool = False
    format_priority: int = 1
    quality_score: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTracks(BaseModel):
    total: int
    page: int
    size: int
    items: list[TrackOut]


# ----------------------------- Playlists -----------------------------
class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    folder_id: Optional[int] = None


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[int] = None


class PlaylistOut(BaseModel):
    id: int
    name: str
    owner_id: int
    is_system: bool
    description: Optional[str] = None
    folder_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    track_count: int = 0

    model_config = {"from_attributes": True}


class PlaylistDetail(PlaylistOut):
    items: list["PlaylistItemOut"] = []


class PlaylistItemOut(BaseModel):
    id: int
    track_id: int
    position: int
    added_at: datetime
    track: Optional[TrackOut] = None

    model_config = {"from_attributes": True}


class AddTracksRequest(BaseModel):
    track_ids: list[int]


class ReorderRequest(BaseModel):
    track_id: int
    new_position: int


# ----------------------------- PlaylistFolders -----------------------------
class PlaylistFolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class PlaylistFolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class PlaylistFolderOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ----------------------------- WatchDirs -----------------------------
class WatchDirCreate(BaseModel):
    path: str
    recursive: bool = True
    enabled: bool = True


class WatchDirUpdate(BaseModel):
    recursive: Optional[bool] = None
    enabled: Optional[bool] = None


class WatchDirOut(BaseModel):
    id: int
    path: str
    recursive: bool
    enabled: bool
    last_scanned_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------------- Scan -----------------------------
class ScanRequest(BaseModel):
    watch_dir_id: Optional[int] = None


class ScanTaskOut(BaseModel):
    id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_files: int
    processed_files: int
    new_tracks: int
    updated_tracks: int
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


# ----------------------------- NodeTask -----------------------------
class TaskSubmitRequest(BaseModel):
    """提交任务请求"""
    task_type: str = Field(..., description="scan|upload|playlist_add|...")
    priority: int = Field(default=0, description="10=用户交互, 0=默认, -10=后台")
    payload: Optional[dict] = Field(default=None, description="任务参数 JSON")


class NodeTaskOut(BaseModel):
    """任务状态响应"""
    id: int
    task_type: str
    status: str
    priority: int
    payload: Optional[dict] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    progress: int = 0
    submitted_by: Optional[str] = None
    submitted_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NodeTaskList(BaseModel):
    """任务列表（分页）"""
    total: int
    page: int
    size: int
    items: list[NodeTaskOut]


# ----------------------------- Track Delete -----------------------------
class TrackDeleteResult(BaseModel):
    """track_delete 任务结果（1.2.1）

    作为 NodeTask.result 字段返回；前端轮询任务完成后解析此结构。
    """
    track_id: int
    file_deleted: bool = False
    file_missing: bool = False
    removed_node_playlist_items: int = 0
    relative_path: Optional[str] = None
    warning: Optional[str] = None


# ----------------------------- Users -----------------------------
class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


# ----------------------------- Permissions -----------------------------
class PermissionCreate(BaseModel):
    playlist_id: int
    user_id: int


class PermissionOut(BaseModel):
    id: int
    playlist_id: int
    user_id: int
    granted_at: datetime
    granted_by: Optional[int] = None

    model_config = {"from_attributes": True}


# ----------------------------- Dedup -----------------------------
class DedupConfigOut(BaseModel):
    id: int
    fields: list[str]
    duration_tolerance: float
    enabled: bool

    model_config = {"from_attributes": True}


class DedupConfigUpdate(BaseModel):
    fields: Optional[list[str]] = None
    duration_tolerance: Optional[float] = None
    enabled: Optional[bool] = None


class DedupGroup(BaseModel):
    group_key: str
    track_ids: list[int]
    tracks: list[TrackOut] = []


# ----------------------------- Quality -----------------------------
class UpgradeCandidate(BaseModel):
    current_track_id: int
    candidates: list[TrackOut]
    best_candidate_id: Optional[int] = None


class ReplaceRequest(BaseModel):
    playlist_id: int
    old_track_id: int
    new_track_id: int


# ----------------------------- Metadata -----------------------------
class MetadataPreviewRequest(BaseModel):
    track_ids: list[int]


class FieldOverview(BaseModel):
    value: Optional[str] = None
    is_uniform: bool


class MetadataPreview(BaseModel):
    track_ids: list[int]
    fields: dict[str, FieldOverview]


class MetadataUpdateFieldRequest(BaseModel):
    track_ids: list[int]
    field: str
    value: Optional[str] = None


class MetadataBatchUpdateRequest(BaseModel):
    """多字段批量保存：一次请求更新多个字段，所有 track_ids 都会被写入这些字段值。"""
    track_ids: list[int]
    updates: dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="{field: value} 字段值映射，None 或空串表示清空",
    )


class MetadataBatchUpdateResult(BaseModel):
    updated: int
    fields: list[str] = []
    skipped: list[dict] = []


class RenameRequest(BaseModel):
    track_ids: list[int]
    template: str
    exceptions: list[int] = Field(default_factory=list)


class RenamePreviewItem(BaseModel):
    track_id: int
    old_path: str
    new_path: str


class RenamePreview(BaseModel):
    items: list[RenamePreviewItem]


class RenameResult(BaseModel):
    success: list[int] = []
    failed: list[dict] = []


# 前向引用修复
TokenResponse.model_rebuild()
PlaylistDetail.model_rebuild()
