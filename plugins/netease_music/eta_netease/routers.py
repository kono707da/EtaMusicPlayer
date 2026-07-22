"""网易云插件 FastAPI 路由

所有路由挂在主应用的 /api/netease 前缀下。
扫码登录支持 SSE 推送轮询，避免前端反复轮询。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

import qrcode
import qrcode.image.svg
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from eta_netease import (
    api_login,
    api_playlist,
    api_recommend,
    api_search,
)
from eta_netease.accounts import (
    clear_current_cache,
    delete_account,
    get_current_account,
    list_accounts,
    switch_account,
)
from eta_netease.client import NcmError, request_eapi

logger = logging.getLogger("etamusic.plugins.netease")

router = APIRouter(prefix="/api/netease", tags=["netease"])


# ===== 错误处理工具 =====

def _err(e: Exception, context: str = "") -> HTTPException:
    """把异常转成 HTTPException"""
    if isinstance(e, NcmError):
        msg = f'[{e.code}] {e.message}'
        if context:
            msg = f'{context}: {msg}'
        # 截断到 200 字符以内
        if len(msg) > 200:
            msg = msg[:200]
        return HTTPException(status_code=400, detail=msg)
    msg = str(e)[:200]
    if context:
        msg = f'{context}: {msg}'
    return HTTPException(status_code=500, detail=msg)


def _require_login() -> dict:
    """检查登录状态，返回当前账号信息，未登录抛 401"""
    acc = get_current_account()
    if not acc:
        raise HTTPException(status_code=401, detail='未登录网易云账号')
    return acc


# ===== 多账号管理 =====

@router.get('/accounts')
def get_accounts():
    """列出所有账号"""
    return {'accounts': list_accounts(), 'current': get_current_account() and get_current_account().get('ncm_uid')}


@router.post('/accounts/switch')
def post_switch_account(ncm_uid: str = Query(...)):
    """切换当前账号"""
    acc = switch_account(ncm_uid)
    if not acc:
        raise HTTPException(status_code=404, detail='账号不存在')
    return {'account': {'ncm_uid': acc['ncm_uid'], 'nickname': acc['nickname'],
                        'avatar_url': acc.get('avatar_url'), 'vip_type': acc.get('vip_type')}}


@router.delete('/accounts/{ncm_uid}')
def post_delete_account(ncm_uid: str):
    """删除账号"""
    if not delete_account(ncm_uid):
        raise HTTPException(status_code=404, detail='账号不存在')
    return {'detail': '账号已删除'}


# ===== 登录 =====

@router.get('/login/qrcode/key')
def get_qrcode_key():
    """生成二维码登录 key"""
    try:
        r = api_login.qrcode_generate_key()
        return r
    except Exception as e:
        raise _err(e, '生成二维码失败')


@router.get('/login/qrcode/url')
def get_qrcode_url(unikey: str = Query(...)):
    """构造二维码 URL（前端可用此 URL 自行生成二维码）"""
    try:
        r = api_login.qrcode_generate_url(unikey)
        return r
    except Exception as e:
        raise _err(e, '构造二维码 URL 失败')


@router.get('/login/qrcode/image')
def get_qrcode_image(unikey: str = Query(...)):
    """直接返回二维码 SVG 图片"""
    try:
        url = f'https://music.163.com/login?codekey={unikey}'
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(url, image_factory=factory)
        from io import BytesIO
        buf = BytesIO()
        img.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type='image/svg+xml')
    except Exception as e:
        raise _err(e, '生成二维码图片失败')


@router.get('/login/qrcode/poll')
def get_qrcode_poll(unikey: str = Query(...)):
    """单次查询二维码扫码状态（前端轮询用）

    返回 code:
    - 800: 二维码过期
    - 801: 等待扫码
    - 802: 已扫码待确认
    - 803: 登录成功
    - 8821: 风控拒绝
    """
    try:
        r = api_login.qrcode_check_status(unikey)
        # 803 登录成功，处理 cookie 持久化
        if r.get('code') == 803:
            # eapi 模式下 cookie 在 set-cookie 响应头，需要 client 层捕获
            # 这里直接调用 login_status 验证当前 cookie 是否生效
            try:
                status = api_login.login_status()
                profile = status.get('profile') or {}
                account = status.get('account') or {}
                ncm_uid = account.get('id') or profile.get('userId')
                if ncm_uid:
                    # 从当前 session 拿 cookie（client 层应已保存）
                    from eta_netease.client import _get_session
                    cookies = {c.name: c.value for c in _get_session().cookies}
                    api_login.handle_login_success(r, cookies)
            except Exception as inner:
                logger.warning('登录成功但保存账号失败: %s', inner)
        return r
    except Exception as e:
        raise _err(e, '查询扫码状态失败')


@router.get('/login/qrcode/wait')
async def get_qrcode_wait(unikey: str = Query(...), timeout: int = Query(120, ge=10, le=300)):
    """SSE 模式：等待扫码登录完成，自动轮询推送状态

    前端用 EventSource 监听，每秒收到一次状态。
    收到 code=803 时连接关闭，登录完成。
    """
    async def event_stream():
        start = asyncio.get_event_loop().time()
        while True:
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > timeout:
                yield f'data: {json.dumps({"code": 800, "message": "二维码已过期"})}\n\n'
                return
            try:
                r = api_login.qrcode_check_status(unikey)
                code = r.get('code')
                yield f'data: {json.dumps(r)}\n\n'
                if code == 803:
                    # 登录成功，处理 cookie
                    try:
                        from eta_netease.client import _get_session
                        cookies = {c.name: c.value for c in _get_session().cookies}
                        api_login.handle_login_success(r, cookies)
                    except Exception as inner:
                        logger.warning('登录成功但保存账号失败: %s', inner)
                    return
                if code == 800 or code == 8821:
                    # 过期或被拒绝，结束
                    return
            except Exception as e:
                logger.warning('SSE 轮询失败: %s', e)
                yield f'data: {json.dumps({"code": -1, "message": str(e)[:100]})}\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(event_stream(), media_type='text/event-stream')


@router.get('/login/status')
def get_login_status():
    """查询当前账号登录状态"""
    try:
        return api_login.login_status()
    except Exception as e:
        raise _err(e, '查询登录状态失败')


@router.post('/login/refresh')
def post_login_refresh():
    """刷新登录 token"""
    try:
        return api_login.login_refresh()
    except Exception as e:
        raise _err(e, '刷新登录失败')


# ===== 搜索 =====

@router.get('/search')
def get_search(keyword: str = Query(...), type: int = Query(1, ge=1),
               limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
    """搜索（type: 1=歌曲 10=专辑 100=歌手 1000=歌单 1002=用户 1004=MV 1006=歌词 1009=电台 1014=视频）"""
    try:
        return api_search.cloudsearch(keyword, type, limit, offset)
    except Exception as e:
        raise _err(e, '搜索失败')


@router.get('/search/hot')
def get_search_hot():
    """热门搜索"""
    try:
        return api_search.search_hot()
    except Exception as e:
        raise _err(e, '获取热搜失败')


@router.get('/search/hot/detail')
def get_search_hot_detail():
    """热门搜索详情"""
    try:
        return api_search.search_hot_detail()
    except Exception as e:
        raise _err(e, '获取热搜详情失败')


@router.get('/search/suggest')
def get_search_suggest(keywords: str = Query(...)):
    """搜索建议"""
    try:
        return api_search.search_suggest(keywords)
    except Exception as e:
        raise _err(e, '获取搜索建议失败')


# ===== 歌曲 =====

@router.get('/song/detail')
def get_song_detail(ids: str = Query(..., description='逗号分隔的歌曲 ID 列表')):
    """歌曲详情（批量）"""
    try:
        song_ids = [int(i) for i in ids.split(',') if i.strip()]
        return api_search.song_detail(song_ids)
    except ValueError:
        raise HTTPException(status_code=400, detail='歌曲 ID 格式错误')
    except Exception as e:
        raise _err(e, '获取歌曲详情失败')


@router.get('/song/url')
def get_song_url(ids: str = Query(...), level: str = Query('standard')):
    """播放 URL（批量）

    level: standard, exhigh, lossless, hires
    """
    try:
        song_ids = [int(i) for i in ids.split(',') if i.strip()]
        return api_search.song_url_v1(song_ids, level=level)
    except ValueError:
        raise HTTPException(status_code=400, detail='歌曲 ID 格式错误')
    except Exception as e:
        raise _err(e, '获取播放 URL 失败')


@router.get('/song/download_url')
def get_song_download_url(id: int = Query(...), level: str = Query('standard')):
    """下载 URL（单曲）"""
    try:
        return api_search.song_download_url(id, level=level)
    except Exception as e:
        raise _err(e, '获取下载 URL 失败')


@router.get('/song/lyric')
def get_song_lyric(id: int = Query(...), new: bool = Query(False)):
    """歌词"""
    try:
        return api_search.lyric_new(id) if new else api_search.lyric(id)
    except Exception as e:
        raise _err(e, '获取歌词失败')


# ===== 推荐 =====

@router.get('/recommend/personalized')
def get_personalized(limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
    """推荐歌单（匿名可用）"""
    try:
        return api_recommend.personalized_playlist(limit, offset)
    except Exception as e:
        raise _err(e, '获取推荐歌单失败')


@router.get('/recommend/newsong')
def get_recommend_newsong(limit: int = Query(10, ge=1, le=100), areaId: int = Query(0)):
    """推荐新歌（匿名可用）"""
    try:
        return api_recommend.personalized_newsong(limit, areaId)
    except Exception as e:
        raise _err(e, '获取推荐新歌失败')


@router.get('/recommend/songs')
def get_recommend_songs():
    """每日推荐歌曲（需登录）"""
    _require_login()
    try:
        return api_recommend.recommend_songs()
    except Exception as e:
        raise _err(e, '获取每日推荐失败')


@router.get('/recommend/resource')
def get_recommend_resource():
    """推荐歌单（需登录，与 personalized 不同，这是登录后个性化推荐）"""
    _require_login()
    try:
        return api_recommend.recommend_resource()
    except Exception as e:
        raise _err(e, '获取推荐歌单失败')


@router.get('/recommend/history')
def get_recommend_history():
    """历史推荐歌曲（需登录）"""
    _require_login()
    try:
        return api_recommend.history_recommend_songs()
    except Exception as e:
        raise _err(e, '获取历史推荐失败')


# ===== 排行榜 =====

@router.get('/toplist')
def get_toplist():
    """所有排行榜"""
    try:
        return api_recommend.toplist()
    except Exception as e:
        raise _err(e, '获取排行榜列表失败')


@router.get('/toplist/detail')
def get_toplist_detail(id: int = Query(...)):
    """排行榜详情（含曲目）"""
    try:
        return api_recommend.toplist_detail(id)
    except Exception as e:
        raise _err(e, '获取排行榜详情失败')


@router.get('/toplist/detail/v2')
def get_toplist_detail_v2(id: int = Query(...)):
    """排行榜详情 v2"""
    try:
        return api_recommend.toplist_detail_v2(id)
    except Exception as e:
        raise _err(e, '获取排行榜详情失败')


@router.get('/top/song')
def get_top_song(areaId: int = Query(0)):
    """新歌速递（areaId: 0=全部 7=华语 96=欧美 8=日本 16=韩国）"""
    try:
        return api_recommend.top_song(areaId)
    except Exception as e:
        raise _err(e, '获取新歌速递失败')


# ===== 歌单查看 =====

@router.get('/playlist/detail')
def get_playlist_detail(id: int = Query(...)):
    """歌单详情"""
    try:
        return api_playlist.playlist_detail(id)
    except Exception as e:
        raise _err(e, '获取歌单详情失败')


@router.get('/playlist/track/all')
def get_playlist_track_all(id: int = Query(...)):
    """歌单全部曲目"""
    try:
        return api_playlist.playlist_track_all(id)
    except Exception as e:
        raise _err(e, '获取歌单曲目失败')


@router.post('/playlist/subscribe')
def post_playlist_subscribe(id: int = Query(...), subscribe: bool = Query(True)):
    """收藏/取消收藏歌单"""
    _require_login()
    try:
        return api_playlist.playlist_subscribe(id, subscribe)
    except Exception as e:
        raise _err(e, '收藏歌单失败')


@router.get('/playlist/mylike')
def get_playlist_mylike():
    """我喜欢的音乐 ID 列表"""
    _require_login()
    try:
        return api_playlist.playlist_mylike()
    except Exception as e:
        raise _err(e, '获取我喜欢的音乐失败')


@router.get('/playlist/subscribers')
def get_playlist_subscribers(id: int = Query(...), limit: int = Query(20, ge=1, le=100),
                              offset: int = Query(0, ge=0)):
    """歌单收藏者"""
    try:
        return api_playlist.playlist_subscribers(id, limit, offset)
    except Exception as e:
        raise _err(e, '获取歌单收藏者失败')


@router.get('/playlist/catlist')
def get_playlist_catlist(limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
    """歌单分类"""
    try:
        return api_playlist.playlist_catlist(limit, offset)
    except Exception as e:
        raise _err(e, '获取歌单分类失败')


@router.get('/playlist/highquality/tags')
def get_playlist_highquality_tags():
    """精品歌单标签"""
    try:
        return api_playlist.playlist_highquality_tags()
    except Exception as e:
        raise _err(e, '获取精品歌单标签失败')


# ===== 歌单管理（需登录） =====

class PlaylistCreateReq(BaseModel):
    name: str
    privacy: int = 0


class PlaylistTrackOpReq(BaseModel):
    playlist_id: int
    track_ids: list[int]


class PlaylistUpdateNameReq(BaseModel):
    playlist_id: int
    name: str


@router.post('/playlist/create')
def post_playlist_create(req: PlaylistCreateReq):
    """创建歌单"""
    _require_login()
    try:
        return api_playlist.playlist_create(req.name, req.privacy)
    except Exception as e:
        raise _err(e, '创建歌单失败')


@router.delete('/playlist/{playlist_id}')
def delete_playlist(playlist_id: int):
    """删除歌单"""
    _require_login()
    try:
        return api_playlist.playlist_delete(playlist_id)
    except Exception as e:
        raise _err(e, '删除歌单失败')


@router.post('/playlist/track/add')
def post_playlist_track_add(req: PlaylistTrackOpReq):
    """添加歌曲到歌单"""
    _require_login()
    try:
        return api_playlist.playlist_track_add(req.playlist_id, req.track_ids)
    except Exception as e:
        raise _err(e, '添加歌曲失败')


@router.post('/playlist/track/delete')
def post_playlist_track_delete(req: PlaylistTrackOpReq):
    """从歌单删除歌曲"""
    _require_login()
    try:
        return api_playlist.playlist_track_delete(req.playlist_id, req.track_ids)
    except Exception as e:
        raise _err(e, '删除歌曲失败')


@router.post('/playlist/update/name')
def post_playlist_update_name(req: PlaylistUpdateNameReq):
    """修改歌单名称"""
    _require_login()
    try:
        return api_playlist.playlist_update_name(req.playlist_id, req.name)
    except Exception as e:
        raise _err(e, '修改歌单名称失败')


# ===== 关注用户 =====

@router.get('/user/follows')
def get_user_follows(uid: int = Query(...), limit: int = Query(30, ge=1, le=100),
                      offset: int = Query(0, ge=0)):
    """关注的人"""
    try:
        return api_playlist.user_follows(uid, limit, offset)
    except Exception as e:
        raise _err(e, '获取关注列表失败')


@router.get('/user/followeds')
def get_user_followeds(uid: int = Query(...), limit: int = Query(30, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    """粉丝"""
    try:
        return api_playlist.user_followeds(uid, limit, offset)
    except Exception as e:
        raise _err(e, '获取粉丝列表失败')


@router.get('/user/detail')
def get_user_detail(uid: int = Query(...)):
    """用户详情"""
    try:
        return api_playlist.user_detail(uid)
    except Exception as e:
        raise _err(e, '获取用户详情失败')


@router.get('/user/playlist')
def get_user_playlist(uid: int = Query(...), limit: int = Query(30, ge=1, le=100),
                       offset: int = Query(0, ge=0)):
    """用户歌单"""
    try:
        return api_playlist.user_playlist(uid, limit, offset)
    except Exception as e:
        raise _err(e, '获取用户歌单失败')


@router.get('/user/self/playlists')
def get_my_playlists():
    """当前账号的歌单（便捷接口，自动用当前账号 uid 查询）"""
    acc = _require_login()
    try:
        uid = int(acc['ncm_uid'])
        return api_playlist.user_playlist(uid)
    except Exception as e:
        raise _err(e, '获取我的歌单失败')


# ===== 下载 =====

class DownloadSongReq(BaseModel):
    song_ids: list[int]
    level: str = 'exhigh'
    target_base_url: str = 'local_node'
    target_watch_dir_id: int = 1
    target_subdir: Optional[str] = None


class DownloadPlaylistReq(BaseModel):
    playlist_id: int
    level: str = 'exhigh'
    target_base_url: str = 'local_node'
    target_watch_dir_id: int = 1
    target_subdir: Optional[str] = None
    song_ids: Optional[list[int]] = None  # 指定下载歌单中的部分歌曲


@router.post('/download/songs')
def post_download_songs(req: DownloadSongReq):
    """下载多首歌曲到节点"""
    _require_login()
    from eta_netease.database import SessionLocal, init_db
    from eta_netease.models import DownloadTask
    from eta_netease.downloader import start_download_task

    init_db()
    if not req.song_ids:
        raise HTTPException(status_code=400, detail='未指定歌曲')

    # 获取歌曲详情
    try:
        detail_resp = api_search.song_detail(req.song_ids)
    except Exception as e:
        raise _err(e, '获取歌曲详情失败')

    songs = []
    for s in detail_resp.get('songs', []):
        artists = s.get('ar', []) or s.get('artists', [])
        artist_str = ' / '.join(a.get('name', '') for a in artists if a.get('name'))
        songs.append({
            'song_id': s.get('id'),
            'name': s.get('name', ''),
            'artist': artist_str,
            'album': (s.get('al', {}) or {}).get('name', ''),
            'album_pic': (s.get('al', {}) or {}).get('picUrl', ''),
        })

    if not songs:
        raise HTTPException(status_code=400, detail='未找到歌曲信息')

    db = SessionLocal()
    try:
        task = DownloadTask(
            source_type='song',
            source_title=songs[0].get('name', '批量下载'),
            songs_json=songs,
            selected_song_ids=None,
            target_base_url=req.target_base_url,
            target_watch_dir_id=req.target_watch_dir_id,
            target_subdir=req.target_subdir,
            level=req.level,
            status='pending',
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        start_download_task(task.id)
        return {'task_id': task.id, 'total': len(songs), 'message': f'已创建下载任务，共 {len(songs)} 首'}
    finally:
        db.close()


@router.post('/download/playlist')
def post_download_playlist(req: DownloadPlaylistReq):
    """下载整个歌单或歌单中的指定歌曲"""
    _require_login()
    from eta_netease.database import SessionLocal, init_db
    from eta_netease.models import DownloadTask
    from eta_netease.downloader import start_download_task

    init_db()

    # 获取歌单信息
    try:
        pl_detail = api_playlist.playlist_detail(req.playlist_id)
        pl_name = pl_detail.get('playlist', {}).get('name', f'歌单{req.playlist_id}')
    except Exception:
        pl_name = f'歌单{req.playlist_id}'

    # 获取歌单全部曲目
    try:
        tracks_resp = api_playlist.playlist_track_all(req.playlist_id)
    except Exception as e:
        raise _err(e, '获取歌单曲目失败')

    all_tracks = tracks_resp.get('songs', []) or tracks_resp.get('data', {}).get('songs', [])
    if req.song_ids:
        selected_set = set(req.song_ids)
        all_tracks = [t for t in all_tracks if t.get('id') in selected_set]

    if not all_tracks:
        raise HTTPException(status_code=400, detail='歌单中未找到可下载的歌曲')

    songs = []
    for t in all_tracks:
        artists = t.get('ar', []) or t.get('artists', [])
        artist_str = ' / '.join(a.get('name', '') for a in artists if a.get('name'))
        songs.append({
            'song_id': t.get('id'),
            'name': t.get('name', ''),
            'artist': artist_str,
            'album': (t.get('al', {}) or {}).get('name', ''),
            'album_pic': (t.get('al', {}) or {}).get('picUrl', ''),
        })

    db = SessionLocal()
    try:
        task = DownloadTask(
            source_type='playlist',
            source_id=str(req.playlist_id),
            source_title=pl_name,
            songs_json=songs,
            selected_song_ids=None,
            target_base_url=req.target_base_url,
            target_watch_dir_id=req.target_watch_dir_id,
            target_subdir=req.target_subdir,
            level=req.level,
            status='pending',
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        start_download_task(task.id)
        return {'task_id': task.id, 'total': len(songs), 'message': f'已创建下载任务: {pl_name}，共 {len(songs)} 首'}
    finally:
        db.close()


@router.get('/download/tasks')
def get_download_tasks(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询下载任务列表"""
    from eta_netease.database import SessionLocal, init_db
    from eta_netease.models import DownloadTask
    from sqlalchemy import desc

    init_db()
    db = SessionLocal()
    try:
        q = db.query(DownloadTask)
        if status:
            q = q.filter(DownloadTask.status == status)
        total = q.count()
        tasks = q.order_by(desc(DownloadTask.created_at)).offset((page - 1) * size).limit(size).all()
        return {
            'total': total,
            'page': page,
            'size': size,
            'items': [_task_to_dict(t) for t in tasks],
        }
    finally:
        db.close()


@router.get('/download/tasks/{task_id}')
def get_download_task_detail(task_id: int):
    """查询下载任务详情（含文件状态）"""
    from eta_netease.database import SessionLocal, init_db
    from eta_netease.models import DownloadTask, DownloadFileStatus

    init_db()
    db = SessionLocal()
    try:
        task = db.get(DownloadTask, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail='任务不存在')
        result = _task_to_dict(task)
        files = (
            db.query(DownloadFileStatus)
            .filter(DownloadFileStatus.task_id == task_id)
            .order_by(DownloadFileStatus.id)
            .all()
        )
        result['files'] = [
            {
                'song_id': f.song_id,
                'file_path': f.file_path,
                'status': f.status,
                'size': f.size,
                'done': f.done,
                'error': f.error,
                'saved_to': f.saved_to,
                'was_ncm': f.was_ncm,
                'decrypted_format': f.decrypted_format,
            }
            for f in files
        ]
        return result
    finally:
        db.close()


@router.post('/download/tasks/{task_id}/cancel')
def post_cancel_download(task_id: int):
    """取消下载任务"""
    from eta_netease.downloader import cancel_download_task

    ok = cancel_download_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail='任务不存在或已完成')
    return {'detail': '任务已取消'}


def _task_to_dict(task) -> dict:
    return {
        'id': task.id,
        'source_type': task.source_type,
        'source_id': task.source_id,
        'source_title': task.source_title,
        'status': task.status,
        'total_files': task.total_files,
        'completed_files': task.completed_files,
        'skipped_files': task.skipped_files,
        'failed_files': task.failed_files,
        'current_file': task.current_file,
        'current_file_size': task.current_file_size,
        'current_file_done': task.current_file_done,
        'error_message': task.error_message,
        'level': task.level,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
        'finished_at': task.finished_at.isoformat() if task.finished_at else None,
    }
