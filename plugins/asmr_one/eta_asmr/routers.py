"""asmr_one API 路由

挂在主应用的 /api/asmr 前缀下。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from eta_asmr.asmr_client import AsmrClient, AsmrError, DEFAULT_TIMEOUT, flatten_file_tree
from eta_asmr.database import get_db
from eta_asmr.downloader import (
    cancel_download_task,
    start_download_task,
)
from eta_asmr.models import DownloadFileStatus, DownloadTask, Setting

router = APIRouter(prefix="/api/asmr", tags=["asmr"])

DEFAULT_SETTINGS = {
    "proxy_url": "http://127.0.0.1:7897",
    "verify_ssl": "true",
    "subdir": "ASMR",
    "default_watch_dir_id": "",
}


def _ensure_total_page(data: dict) -> dict:
    """asmr.one 不返回 totalPage，这里根据 totalCount/pageSize 补上。"""
    if not isinstance(data, dict):
        return data
    pag = data.get("pagination")
    if isinstance(pag, dict) and pag.get("totalPage") in (None, "", 0):
        total = pag.get("totalCount") or 0
        size = pag.get("pageSize") or 1
        if size < 1:
            size = 1
        pag["totalPage"] = max(1, (total + size - 1) // size)
    return data

# ===== 设置 =====

def _get_settings_dict(db: Session) -> dict[str, str]:
    rows = db.query(Setting).all()
    out = dict(DEFAULT_SETTINGS)
    for r in rows:
        out[r.key] = r.value
    return out


def _save_settings(db: Session, data: dict[str, Any]) -> dict[str, str]:
    out = dict(DEFAULT_SETTINGS)
    for r in db.query(Setting).all():
        out[r.key] = r.value
    for k, v in data.items():
        if k not in DEFAULT_SETTINGS:
            continue
        s = db.query(Setting).filter(Setting.key == k).one_or_none()
        if s is None:
            s = Setting(key=k, value=str(v) if v is not None else "")
            db.add(s)
        else:
            s.value = str(v) if v is not None else ""
        out[k] = str(v) if v is not None else ""
    db.commit()
    return out


# ===== Token 存取 =====

TOKEN_KEY = "asmr_one_token"


def _get_token(db: Session) -> Optional[str]:
    s = db.query(Setting).filter(Setting.key == TOKEN_KEY).one_or_none()
    return s.value if s else None


def _set_token(db: Session, token: Optional[str]) -> None:
    s = db.query(Setting).filter(Setting.key == TOKEN_KEY).one_or_none()
    if s is None:
        s = Setting(key=TOKEN_KEY, value=token or "")
        db.add(s)
    else:
        s.value = token or ""
    db.commit()


def _clear_token(db: Session) -> None:
    s = db.query(Setting).filter(Setting.key == TOKEN_KEY).one_or_none()
    if s:
        s.value = ""
        db.commit()


def _require_token(db: Session) -> str:
    """获取 token，没有则抛 401"""
    token = _get_token(db)
    if not token:
        raise HTTPException(status_code=401, detail="未登录 asmr.one")
    return token


class SettingsUpdate(BaseModel):
    proxy_url: Optional[str] = None
    verify_ssl: Optional[str] = None
    subdir: Optional[str] = None
    default_watch_dir_id: Optional[str] = None


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)) -> dict:
    return _get_settings_dict(db)


@router.put("/settings")
def update_settings(
    payload: SettingsUpdate, db: Session = Depends(get_db)
) -> dict:
    data = payload.model_dump(exclude_none=True)
    return _save_settings(db, data)


# ===== 工具 =====

def _make_client(db: Session) -> AsmrClient:
    settings = _get_settings_dict(db)
    proxy = settings.get("proxy_url") or None
    verify_ssl = settings.get("verify_ssl", "true").lower() not in ("false", "0", "no")
    return AsmrClient(proxy_url=proxy, verify_ssl=verify_ssl)


# ===== 搜索 / 作品 / 文件树 / 封面 =====

@router.get("/search")
def search(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    order_by: str = Query("create_date"),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    subtitle: int = Query(0, ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict:
    client = _make_client(db)
    try:
        return _ensure_total_page(client.search(
            keyword, page=page, page_size=page_size, order_by=order_by, sort=sort, subtitle=subtitle
        ))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/works")
def list_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    order_by: str = Query("create_date"),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    subtitle: int = Query(0, ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict:
    """列出全部作品（支持排序）"""
    client = _make_client(db)
    try:
        return _ensure_total_page(client.list_works(
            page=page, page_size=page_size, order_by=order_by, sort=sort, subtitle=subtitle
        ))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/tags/{tag_id}/works")
def list_by_tag(
    tag_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    order_by: str = Query("create_date"),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    subtitle: int = Query(0, ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict:
    """按标签筛选作品"""
    client = _make_client(db)
    try:
        return _ensure_total_page(client.list_by_tag(
            tag_id, page=page, page_size=page_size, order_by=order_by, sort=sort, subtitle=subtitle
        ))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/vas/{va_id}/works")
def list_by_va(
    va_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    order_by: str = Query("create_date"),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    subtitle: int = Query(0, ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict:
    """按声优筛选作品"""
    client = _make_client(db)
    try:
        return _ensure_total_page(client.list_by_va(
            va_id, page=page, page_size=page_size, order_by=order_by, sort=sort, subtitle=subtitle
        ))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/circles/{circle_id}/works")
def list_by_circle(
    circle_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    order_by: str = Query("create_date"),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    subtitle: int = Query(0, ge=0, le=1),
    db: Session = Depends(get_db),
) -> dict:
    """按社团筛选作品"""
    client = _make_client(db)
    try:
        return _ensure_total_page(client.list_by_circle(
            circle_id, page=page, page_size=page_size, order_by=order_by, sort=sort, subtitle=subtitle
        ))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/works/{work_id}")
def get_work(work_id: int, db: Session = Depends(get_db)) -> dict:
    client = _make_client(db)
    try:
        return client.get_work(work_id)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/works/{work_id}/tracks")
def get_work_tracks(work_id: int, db: Session = Depends(get_db)) -> dict:
    """返回拍平后的文件列表，方便前端展示与勾选"""
    client = _make_client(db)
    try:
        tree = client.get_tracks(work_id)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")
    files = flatten_file_tree(tree)
    return {
        "tree": tree,
        "files": files,
        "total": len(files),
        "total_size": sum(int(f.get("size") or 0) for f in files),
    }


@router.get("/cover/{work_id}")
def get_cover(
    work_id: int,
    type: str = Query("main", pattern="^(main|sam|240x240)$"),
    db: Session = Depends(get_db),
) -> Response:
    client = _make_client(db)
    try:
        data = client.get_cover_bytes(work_id, cover_type=type)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"封面获取失败: {e}")
    return Response(content=data, media_type="image/jpeg")


@router.get("/preview/text")
def preview_text(
    url: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    """代理获取 asmr.one 文本文件内容（避免前端 CORS 限制）

    只允许 asmr.one / asmr.one 域名的 URL。
    """
    if not any(d in url for d in ("asmr.one", "asmr.one")):
        raise HTTPException(status_code=400, detail="只允许预览 asmr.one 的文件")
    client = _make_client(db)
    try:
        r = client.session.get(
            url,
            headers=client._auth_headers(_get_token(db)) if _get_token(db) else {},
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"获取文件失败: {e}")
    try:
        text = r.content.decode("utf-8")
    except UnicodeDecodeError:
        text = r.content.decode("latin-1", errors="replace")
    return Response(content=text, media_type="text/plain; charset=utf-8")


@router.get("/works/{work_id}/info")
def get_work_info(work_id: int, db: Session = Depends(get_db)) -> dict:
    """作品额外信息（workInfo）"""
    client = _make_client(db)
    try:
        return client.get_work_info(work_id)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


# ===== 认证 =====

class LoginPayload(BaseModel):
    name: str
    password: str


class RegisterPayload(BaseModel):
    name: str
    password: str
    recommender_uuid: Optional[str] = None


@router.get("/auth/status")
def auth_status(db: Session = Depends(get_db)) -> dict:
    """检查本地保存的登录状态 + asmr.one 是否允许注册

    注意：不在状态检查时清 token，避免 asmr.one 临时不可达或网络抖动导致登录态丢失。
    仅当用户主动 logout 时才清。
    """
    client = _make_client(db)
    token = _get_token(db)
    try:
        reg_info = client.check_reg_enabled()
    except requests.RequestException:
        reg_info = {"reg": False}
    if not token:
        return {"logged_in": False, "user": None, "reg_enabled": reg_info.get("reg", False)}
    try:
        me = client.check_auth()
    except requests.RequestException as e:
        return {"logged_in": True, "user": None, "reg_enabled": reg_info.get("reg", False), "warning": str(e)}
    user = me.get("user") or {}
    if not user.get("loggedIn"):
        return {"logged_in": False, "user": None, "reg_enabled": reg_info.get("reg", False)}
    return {"logged_in": True, "user": user, "reg_enabled": reg_info.get("reg", False)}


@router.post("/auth/login")
def auth_login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict:
    client = _make_client(db)
    try:
        data = client.login(payload.name, payload.password)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=500, detail="登录返回无 token")
    _set_token(db, token)
    return {"logged_in": True, "user": data.get("user", {}), "token_saved": True}


@router.post("/auth/register")
def auth_register(payload: RegisterPayload, db: Session = Depends(get_db)) -> dict:
    client = _make_client(db)
    try:
        data = client.register(payload.name, payload.password, payload.recommender_uuid)
    except AsmrError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")
    token = data.get("token")
    if token:
        _set_token(db, token)
    return {"registered": True, "user": data.get("user", {}), "token_saved": bool(token)}


@router.post("/auth/logout")
def auth_logout(db: Session = Depends(get_db)) -> dict:
    _clear_token(db)
    return {"logged_in": False}


# ===== 评价 / 评分 =====

class ReviewUpsert(BaseModel):
    work_id: int
    rating: int = Field(ge=0, le=10)
    review_text: str = ""
    progress: str = ""


@router.get("/reviews")
def list_reviews(
    order: str = Query("create_date"),
    sort: str = Query("desc"),
    page: int = Query(1, ge=1),
    filter: str = Query(""),
    db: Session = Depends(get_db),
) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.list_reviews(token, order=order, sort=sort, page=page, filter=filter)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.put("/reviews")
def upsert_review(payload: ReviewUpsert, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.upsert_review(
            token,
            work_id=payload.work_id,
            rating=payload.rating,
            review_text=payload.review_text,
            progress=payload.progress,
        )
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.delete("/reviews")
def delete_review(work_id: int, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.delete_review(token, work_id=work_id)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


# ===== 播放列表 / 收藏 =====

class PlaylistCreate(BaseModel):
    name: str
    privacy: int = 0
    locale: str = "zh-cn"
    description: str = ""
    works: list = []


class PlaylistOps(BaseModel):
    id: str
    works: list


@router.get("/playlists")
def list_playlists(
    page: int = 1,
    page_size: int = 50,
    filter_by: str = "",
    db: Session = Depends(get_db),
) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.list_playlists(token, page=page, page_size=page_size, filter_by=filter_by)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/playlists/default")
def get_default_playlist(db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.get_default_playlist(token)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/playlists/{playlist_id}")
def get_playlist_metadata(playlist_id: str, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.get_playlist_metadata(token, playlist_id)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/playlists/{playlist_id}/works")
def get_playlist_works(
    playlist_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    """获取播放列表内的作品列表（asmr.one 的 metadata 接口不返回作品，需调用此接口）"""
    token = _require_token(db)
    client = _make_client(db)
    try:
        data = client.list_playlist_works(token, playlist_id, page, page_size)
        return _ensure_total_page(data)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: str, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.delete_playlist(token, playlist_id)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/works/{work_id}/in-playlists")
def work_in_playlists(work_id: int, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.get_work_in_my_playlists(token, work_id)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.post("/playlists")
def create_playlist(payload: PlaylistCreate, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.create_playlist(
            token,
            name=payload.name,
            privacy=payload.privacy,
            locale=payload.locale,
            description=payload.description,
            works=payload.works,
        )
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.post("/playlists/add")
def add_to_playlist(payload: PlaylistOps, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.add_works_to_playlist(token, payload.id, payload.works)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.post("/playlists/remove")
def remove_from_playlist(payload: PlaylistOps, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.remove_works_from_playlist(token, payload.id, payload.works)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


# ===== 推荐 =====

@router.get("/popular")
def popular_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
) -> dict:
    """热门作品（无需登录）"""
    client = _make_client(db)
    token = _get_token(db)
    try:
        return _ensure_total_page(client.popular_works(page=page, page_size=page_size, keyword=keyword, token=token))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/recommendations")
def recommend_for_user(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
) -> dict:
    """个性化推荐（需登录）"""
    token = _require_token(db)
    client = _make_client(db)
    try:
        return _ensure_total_page(client.recommend_for_user(token, page=page, page_size=page_size, keyword=keyword))
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


@router.get("/works/{work_id}/neighbors")
def work_neighbors(work_id: int, db: Session = Depends(get_db)) -> dict:
    """相似作品推荐"""
    client = _make_client(db)
    token = _get_token(db)
    try:
        return _ensure_total_page(client.item_neighbors(work_id, token=token))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


class FeedbackPayload(BaseModel):
    type: str = Field(pattern="^(like|dislike|unlike|undislike)$")
    recommender_uuid: str
    item_id: int


@router.post("/feedback")
def recommender_feedback(payload: FeedbackPayload, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.recommender_feedback(token, payload.type, payload.recommender_uuid, payload.item_id)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


# ===== 标签投票 =====

class VotePayload(BaseModel):
    work_id: int
    tag_id: int
    status: int = Field(ge=-1, le=1)


@router.post("/vote")
def vote_work_tag(payload: VotePayload, db: Session = Depends(get_db)) -> dict:
    token = _require_token(db)
    client = _make_client(db)
    try:
        return client.vote_work_tag(token, payload.work_id, payload.tag_id, payload.status)
    except AsmrError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"asmr.one 请求失败: {e}")


# ===== 节点信息（local_node） =====

def _list_local_watch_dirs() -> list[dict]:
    """直接查询 local_node 数据库获取监控目录列表。

    同进程内直接读 DB，避免 HTTP 自调用带来的 token/端口/超时等失败点。
    """
    try:
        from eta_node.database import SessionLocal as LocalSession
        from eta_node.models import WatchDir as LocalWatchDir
    except ImportError:
        return []
    db_local = LocalSession()
    try:
        wds = db_local.query(LocalWatchDir).order_by(LocalWatchDir.id).all()
        return [
            {
                "id": wd.id,
                "path": wd.path,
                "recursive": wd.recursive,
                "enabled": wd.enabled,
                "last_scanned_at": wd.last_scanned_at.isoformat() if wd.last_scanned_at else None,
                "created_at": wd.created_at.isoformat() if wd.created_at else None,
            }
            for wd in wds
        ]
    except Exception:
        return []
    finally:
        db_local.close()


@router.get("/target-nodes")
def list_target_nodes(db: Session = Depends(get_db)) -> dict:
    """列出可下载目标节点

    当前仅支持 local_node（需已加载）。
    预留远程节点接口：若远程节点暴露 /api/upload 之类的接口，可在此扩展。
    """
    try:
        from eta_web.plugins_manager.routers import _loaded_in_process
    except ImportError:
        _loaded_in_process = set()

    nodes: list[dict] = []
    if "local_node" in _loaded_in_process:
        watch_dirs = _list_local_watch_dirs()
        nodes.append(
            {
                "type": "local_node",
                "id": "local_node",
                "name": "本地节点",
                "base_url": "/local_node",
                "writable": True,
                "watch_dirs": watch_dirs,
                "reason": "",
            }
        )
    return {"nodes": nodes, "supported_types": ["local_node"]}


# ===== 下载任务 =====

class DownloadCreate(BaseModel):
    work_id: int
    work_title: str
    source_id: Optional[str] = None
    target_node_id: str = Field(default="local_node")
    watch_dir_id: int
    subdir: Optional[str] = None
    selected_paths: Optional[list[str]] = None
    metadata: Optional[dict] = None


@router.post("/downloads", status_code=201)
def create_download(
    payload: DownloadCreate, db: Session = Depends(get_db)
) -> dict:
    settings = _get_settings_dict(db)
    subdir = payload.subdir if payload.subdir is not None else settings.get("subdir", "ASMR")

    task = DownloadTask(
        work_id=payload.work_id,
        work_title=payload.work_title,
        source_id=payload.source_id,
        target_base_url="/local_node",
        target_watch_dir_id=payload.watch_dir_id,
        target_subdir=subdir,
        status="pending",
        files_json=payload.files,
        selected_paths=payload.selected_paths or [],
        total_files=len(payload.files),
        metadata_json=payload.metadata or None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    start_download_task(task.id)

    return _task_to_dict(task, with_files=False)


@router.get("/downloads")
def list_downloads(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(DownloadTask)
    if status:
        q = q.filter(DownloadTask.status == status)
    tasks = q.order_by(DownloadTask.id.desc()).limit(limit).all()
    return {
        "tasks": [_task_to_dict(t, with_files=False) for t in tasks],
        "total": len(tasks),
    }


@router.get("/downloads/{task_id}")
def get_download(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(DownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _task_to_dict(task, with_files=True, db=db)


@router.post("/downloads/{task_id}/cancel")
def cancel_download(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = db.get(DownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    ok = cancel_download_task(task_id)
    return {"canceled": ok, "task_id": task_id}


@router.delete("/downloads/{task_id}", status_code=204)
def delete_download(task_id: int, db: Session = Depends(get_db)):
    task = db.get(DownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status in ("pending", "running"):
        raise HTTPException(status_code=400, detail="任务进行中，请先取消")
    db.query(DownloadFileStatus).filter(DownloadFileStatus.task_id == task_id).delete()
    db.delete(task)
    db.commit()


class CoverApplyRequest(BaseModel):
    """给已完成的下载任务补/换封面"""
    cover_type: str = Field(..., pattern="^(main|sam|240x240)$")
    cover_mode: str = Field("embed", pattern="^(embed|save|both)$")


@router.post("/downloads/{task_id}/apply-cover")
def apply_cover(
    task_id: int,
    payload: CoverApplyRequest,
    db: Session = Depends(get_db),
) -> dict:
    """对已完成的下载任务，重新拉取指定封面并按模式处理。

    cover_mode:
      - embed: 仅嵌入到音频文件标签
      - save:  仅保存为 cover.jpg 到下载目录
      - both:  嵌入 + 保存 cover.jpg
    """
    from eta_asmr.downloader import _apply_metadata_and_cover, _trigger_local_node_scan

    task = db.get(DownloadTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in ("completed", "partial"):
        raise HTTPException(status_code=400, detail="任务未完成，无法应用封面")

    settings = _get_settings_dict(db)
    proxy = settings.get("proxy_url") or None
    verify_ssl = settings.get("verify_ssl", "true").lower() not in ("false", "0", "no")
    client = AsmrClient(proxy_url=proxy, verify_ssl=verify_ssl)

    meta = task.metadata_json or {}
    meta["cover_type"] = payload.cover_type
    task.metadata_json = meta
    task.cover_applied = False
    db.commit()

    _apply_metadata_and_cover(db, task, client, cover_mode=payload.cover_mode)

    if payload.cover_mode in ("embed", "both"):
        _trigger_local_node_scan()

    return {
        "task_id": task_id,
        "cover_applied": task.cover_applied,
        "cover_type": payload.cover_type,
        "cover_mode": payload.cover_mode,
    }


# ===== 输出辅助 =====

def _task_to_dict(
    task: DownloadTask, with_files: bool = False, db: Optional[Session] = None
) -> dict:
    out = {
        "id": task.id,
        "work_id": task.work_id,
        "work_title": task.work_title,
        "source_id": task.source_id,
        "target_base_url": task.target_base_url,
        "target_watch_dir_id": task.target_watch_dir_id,
        "target_subdir": task.target_subdir,
        "status": task.status,
        "total_files": task.total_files,
        "completed_files": task.completed_files,
        "skipped_files": task.skipped_files,
        "failed_files": task.failed_files,
        "current_file": task.current_file,
        "current_file_size": task.current_file_size,
        "current_file_done": task.current_file_done,
        "error_message": task.error_message,
        "metadata": task.metadata_json,
        "cover_applied": task.cover_applied,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }
    if with_files and db is not None:
        files = (
            db.query(DownloadFileStatus)
            .filter(DownloadFileStatus.task_id == task.id)
            .order_by(DownloadFileStatus.id)
            .all()
        )
        out["files"] = [
            {
                "path": f.file_path,
                "status": f.status,
                "size": f.size,
                "done": f.done,
                "error": f.error,
                "saved_to": f.saved_to,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in files
        ]
    return out
