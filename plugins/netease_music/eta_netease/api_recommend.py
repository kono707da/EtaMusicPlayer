"""网易云推荐 / 排行榜相关 API

参照 NeteaseCloudMusicApiEnhanced 的 module/personalized.js、
personalized_newsong.js、recommend_songs.js、recommend_resource.js、
history_recommend_songs.js、toplist.js、toplist_detail.js、top_song.js、
toplist_detail_v2.js 实现。

所有函数均通过 eapi 接口调用，不在内部检查响应码，
调用方可根据需要自行调用 check_response。
"""
from __future__ import annotations

from eta_netease.client import request_eapi


def personalized_playlist(limit: int = 30, offset: int = 0) -> dict:
    """推荐歌单

    调用 POST /api/personalized/playlist

    Args:
        limit: 返回数量，默认 30
        offset: 偏移量，默认 0

    Returns:
        {'result': [...], 'code': 200}
    """
    payload = {
        'limit': limit,
        'offset': offset,
    }
    return request_eapi('/api/personalized/playlist', payload)


def personalized_newsong(limit: int = 10, areaId: int = 0) -> dict:
    """推荐新歌

    调用 POST /api/personalized/newsong

    Args:
        limit: 返回数量，默认 10
        areaId: 地区 ID，默认 0

    Returns:
        {'result': [...], 'code': 200}
    """
    payload = {
        'limit': limit,
        'areaId': areaId,
    }
    return request_eapi('/api/personalized/newsong', payload)


def recommend_songs() -> dict:
    """每日推荐歌曲（需登录）

    调用 POST /api/v3/discovery/recommend/songs

    Returns:
        {'data': {'dailySongs': [...]}, 'code': 200}
    """
    return request_eapi('/api/v3/discovery/recommend/songs', {})


def recommend_resource() -> dict:
    """推荐歌单（需登录，登录后的个性化推荐）

    调用 POST /api/recommend/resource
    与 personalized_playlist 不同，此接口为登录后的个性化推荐

    Returns:
        {'recommend': [...], 'code': 200}
    """
    return request_eapi('/api/recommend/resource', {})


def history_recommend_songs() -> dict:
    """历史推荐歌曲

    调用 POST /api/discovery/recommend/songs/history/recent

    Returns:
        {'data': {'list': [...]}, 'code': 200}
    """
    return request_eapi('/api/discovery/recommend/songs/history/recent', {})


def toplist() -> dict:
    """所有排行榜列表

    调用 POST /api/toplist

    Returns:
        {'list': [...], 'code': 200}
    """
    return request_eapi('/api/toplist', {})


def toplist_detail(toplist_id: int) -> dict:
    """排行榜详情（含曲目）

    调用 POST /api/playlist/detail/dynamic

    Args:
        toplist_id: 排行榜 ID

    Returns:
        {'playlist': {...}, 'code': 200}
    """
    payload = {
        'id': toplist_id,
    }
    return request_eapi('/api/playlist/detail/dynamic', payload)


def toplist_detail_v2(toplist_id: int) -> dict:
    """排行榜详情 v2

    调用 POST /api/toplist/detail/v2

    Args:
        toplist_id: 排行榜 ID

    Returns:
        {'list': {...}, 'code': 200}
    """
    payload = {
        'id': toplist_id,
    }
    return request_eapi('/api/toplist/detail/v2', payload)


def top_song(area_id: int = 0) -> dict:
    """新歌速递

    调用 POST /api/discovery/new/songs

    Args:
        area_id: 地区 ID，0=全部, 7=华语, 96=欧美, 8=日本, 16=韩国，默认 0

    Returns:
        {'data': [...], 'code': 200}
    """
    payload = {
        'areaId': area_id,
        'total': True,
    }
    return request_eapi('/api/discovery/new/songs', payload)
