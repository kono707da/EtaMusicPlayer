"""网易云歌单管理 + 关注用户相关 API

参照 NeteaseCloudMusicApiEnhanced 的 module/playlist_*.js 与 user_*.js 实现，
所有接口走 eapi 加密通道。

调用方需自行判断返回的 code 是否为 200，本模块不做检查。
"""
import json

from eta_netease.client import request_eapi


# ==================== 歌单查看类 ====================

def playlist_detail(playlist_id: int, s: int = 8) -> dict:
    """获取歌单详情

    Args:
        playlist_id: 歌单 ID
        s: 最近收藏者数量，默认 8

    Returns:
        {'playlist': {...}, 'code': 200}
    """
    payload = {'id': playlist_id, 's': s}
    return request_eapi('/api/v6/playlist/detail', payload)


def playlist_track_all(playlist_id: int, limit: int = 100, offset: int = 0) -> dict:
    """获取歌单全部曲目

    通过设置较大的 n 一次性拉取全部曲目；limit/offset 参数保留以兼容调用方签名，
    实际不在 payload 中使用，需要分页请在外部切片处理。

    Args:
        playlist_id: 歌单 ID
        limit: 预留参数，不发送给服务器
        offset: 预留参数，不发送给服务器

    Returns:
        {'playlist': {'tracks': [...], 'trackCount': ...}, 'code': 200}
    """
    payload = {'id': playlist_id, 'n': 100000, 's': 8}
    return request_eapi('/api/v6/playlist/detail', payload)


def playlist_subscribe(playlist_id: int, subscribe: bool = True) -> dict:
    """收藏 / 取消收藏歌单

    Args:
        playlist_id: 歌单 ID
        subscribe: True=收藏, False=取消收藏

    Returns:
        {'code': 200}
    """
    # 收藏与取消收藏使用不同 URL
    action = 'subscribe' if subscribe else 'unsubscribe'
    payload = {'id': playlist_id}
    return request_eapi(f'/api/playlist/{action}', payload)


def playlist_mylike() -> dict:
    """获取我喜欢的音乐 ID 列表

    Returns:
        {'ids': [...], 'code': 200}
    """
    return request_eapi('/api/song/like/get', {})


def playlist_subscribers(playlist_id: int, limit: int = 20, offset: int = 0) -> dict:
    """获取歌单收藏者列表

    Args:
        playlist_id: 歌单 ID
        limit: 每页数量，默认 20
        offset: 偏移量，默认 0

    Returns:
        {'subscribers': [...], 'code': 200}
    """
    payload = {'id': playlist_id, 'limit': limit, 'offset': offset}
    return request_eapi('/api/playlist/subscribers', payload)


def playlist_catlist(limit: int = 30, offset: int = 0) -> dict:
    """获取歌单分类列表

    Args:
        limit: 每页数量，默认 30
        offset: 偏移量，默认 0

    Returns:
        {'sub': [...], 'all': [...], 'code': 200}
    """
    payload = {'limit': limit, 'offset': offset}
    return request_eapi('/api/playlist/catalogue', payload)


def playlist_highquality_tags() -> dict:
    """获取精品歌单标签

    Returns:
        {'tags': [...], 'code': 200}
    """
    return request_eapi('/api/playlist/highquality/tags', {})


# ==================== 歌单管理类 ====================

def playlist_create(name: str, privacy: int = 0) -> dict:
    """新建歌单

    Args:
        name: 歌单名称
        privacy: 0=普通歌单, 10=隐私歌单

    Returns:
        {'id': ..., 'code': 200}
    """
    payload = {'name': name, 'privacy': privacy}
    return request_eapi('/api/playlist/create', payload)


def playlist_delete(playlist_id: int) -> dict:
    """删除歌单

    Args:
        playlist_id: 歌单 ID

    Returns:
        {'code': 200}
    """
    payload = {'ids': f'[{playlist_id}]'}
    return request_eapi('/api/playlist/delete', payload)


def playlist_track_add(playlist_id: int, track_ids: list[int]) -> dict:
    """向歌单添加曲目

    Args:
        playlist_id: 歌单 ID
        track_ids: 曲目 ID 列表

    Returns:
        {'body': {'code': 200}, 'code': 200}
    """
    payload = {
        'op': 'add',
        'pid': playlist_id,
        'tracks': ','.join(str(t) for t in track_ids),
        'trackIds': json.dumps(track_ids),
    }
    return request_eapi('/api/playlist/manipulate/tracks', payload)


def playlist_track_delete(playlist_id: int, track_ids: list[int]) -> dict:
    """从歌单删除曲目

    Args:
        playlist_id: 歌单 ID
        track_ids: 曲目 ID 列表

    Returns:
        {'body': {'code': 200}, 'code': 200}
    """
    payload = {
        'op': 'del',
        'pid': playlist_id,
        'tracks': ','.join(str(t) for t in track_ids),
        'trackIds': json.dumps(track_ids),
    }
    return request_eapi('/api/playlist/manipulate/tracks', payload)


def playlist_update_name(playlist_id: int, name: str) -> dict:
    """更新歌单名称

    Args:
        playlist_id: 歌单 ID
        name: 新名称

    Returns:
        {'code': 200}
    """
    payload = {'id': playlist_id, 'name': name}
    return request_eapi('/api/playlist/update/name', payload)


# ==================== 关注用户类 ====================

def user_follows(uid: int, limit: int = 30, offset: int = 0) -> dict:
    """获取用户关注的人

    Args:
        uid: 用户 ID
        limit: 每页数量，默认 30
        offset: 偏移量，默认 0

    Returns:
        {'follow': [...], 'code': 200}
    """
    payload = {'uid': uid, 'limit': limit, 'offset': offset}
    return request_eapi('/api/user/follows', payload)


def user_followeds(uid: int, limit: int = 30, offset: int = 0) -> dict:
    """获取用户粉丝

    Args:
        uid: 用户 ID
        limit: 每页数量，默认 30
        offset: 偏移量，默认 0

    Returns:
        {'followeds': [...], 'code': 200}
    """
    payload = {'uid': uid, 'limit': limit, 'offset': offset, 'lastTime': 0}
    return request_eapi('/api/user/followeds', payload)


def user_detail(uid: int) -> dict:
    """获取用户详情

    Args:
        uid: 用户 ID

    Returns:
        {'profile': {...}, 'code': 200}
    """
    payload = {'uid': uid}
    return request_eapi('/api/w/user/get', payload)


def user_playlist(uid: int, limit: int = 30, offset: int = 0) -> dict:
    """获取用户歌单

    Args:
        uid: 用户 ID
        limit: 每页数量，默认 30
        offset: 偏移量，默认 0

    Returns:
        {'playlist': [...], 'code': 200}
    """
    payload = {'uid': uid, 'limit': limit, 'offset': offset, 'includeVideo': True}
    return request_eapi('/api/user/playlist', payload)
