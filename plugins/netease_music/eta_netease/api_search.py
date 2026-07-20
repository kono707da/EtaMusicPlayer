"""网易云搜索 / 歌曲 / 歌词相关 API

参照 NeteaseCloudMusicApiEnhanced 的 module/cloudsearch.js, search_hot.js,
search_hot_detail.js, search_suggest.js, song_detail.js, song_url_v1.js,
song_download_url.js, lyric.js, lyric_new.js 实现。

所有函数均返回原始 JSON dict，不内部调用 check_response，
由调用方自行决定是否抛错。
"""
import json

from eta_netease.client import request_eapi, check_response, NcmError


# =====================================================================
# 搜索类
# =====================================================================

def cloudsearch(keyword: str, search_type: int = 1,
                limit: int = 30, offset: int = 0) -> dict:
    """云搜索（PC 端，返回字段比旧版 /api/search 更全）

    Args:
        keyword: 搜索关键词
        search_type: 搜索类型
            1=歌曲, 10=专辑, 100=歌手, 1000=歌单, 1002=用户,
            1004=MV, 1006=歌词, 1009=主播电台, 1014=视频
        limit: 每页数量
        offset: 偏移量（用于分页）

    Returns:
        {'result': {...}, 'code': 200}
    """
    payload = {
        's': keyword,
        'type': search_type,
        'limit': limit,
        'offset': offset,
    }
    return request_eapi('/api/cloudsearch/pc', payload)


def search_hot() -> dict:
    """热门搜索（简版，仅关键词列表）

    Returns:
        {'result': {'hots': [...]}, 'code': 200}
    """
    return request_eapi('/api/search/hot', {})


def search_hot_detail() -> dict:
    """热门搜索详情（含封面、播放数等元数据）

    Returns:
        {'data': [...], 'code': 200}
    """
    return request_eapi('/api/search/hot/detail', {})


def search_suggest(keywords: str) -> dict:
    """搜索建议（web 端，返回匹配的歌曲/歌单/歌手等建议）

    Args:
        keywords: 关键词

    Returns:
        {'result': {...}, 'code': 200}
    """
    return request_eapi('/api/search/suggest/web', {'s': keywords})


# =====================================================================
# 歌曲类
# =====================================================================

def song_detail(song_ids: list) -> dict:
    """歌曲详情（批量）

    Args:
        song_ids: 歌曲 id 列表

    Returns:
        {'songs': [...], 'code': 200}
    """
    # /api/v3/song/detail 的 c 参数为 JSON 字符串
    payload = {
        'c': json.dumps([{'id': sid} for sid in song_ids]),
    }
    return request_eapi('/api/v3/song/detail', payload)


def song_url_v1(song_ids: list, level: str = 'standard',
                encode_type: str = 'aac') -> dict:
    """歌曲播放 URL（v1，支持多品质 level）

    Args:
        song_ids: 歌曲 id 列表
        level: 音质等级
            standard=标准, exhigh=极高, lossless=无损, hires=Hi-Res
        encode_type: 编码类型，默认 'aac'

    Returns:
        {'data': [{'id':, 'url':, 'br':, 'size':, 'type':, ...}], 'code': 200}
    """
    payload = {
        'ids': json.dumps(song_ids),
        'level': level,
        'encodeType': encode_type,
        'codecs': encode_type,
    }
    return request_eapi('/api/song/enhance/player/url/v1', payload)


def song_download_url(song_id: int, level: str = 'standard',
                      codecs: str = 'aac') -> dict:
    """歌曲下载 URL（单首，返回的 url 通常可直接下载，无需 cookie）

    Args:
        song_id: 歌曲 id
        level: 音质等级
            standard=标准, exhigh=极高, lossless=无损, hires=Hi-Res
        codecs: 编码类型，默认 'aac'

    Returns:
        {'data': {'url':, 'br':, 'size':, ...}, 'code': 200}
    """
    payload = {
        'id': song_id,
        'level': level,
        'codecs': codecs,
    }
    return request_eapi('/api/song/download/url/v1', payload)


# =====================================================================
# 歌词类
# =====================================================================

def lyric(song_id: int) -> dict:
    """歌词（原版接口）

    Args:
        song_id: 歌曲 id

    Returns:
        {'lrc': {'lyric': '...'},          # 原文歌词
         'tlyric': {'lyric': '...'},       # 翻译歌词
         'romalrc': {'lyric': '...'},      # 罗马音歌词
         'code': 200}
    """
    payload = {
        'id': song_id,
        'lv': -1,   # 原文歌词
        'tv': -1,   # 翻译歌词
        'kv': -1,   # 卡拉OK歌词
    }
    return request_eapi('/api/song/lyric', payload)


def lyric_new(song_id: int) -> dict:
    """歌词（新版接口，部分歌曲返回内容更完整）

    Args:
        song_id: 歌曲 id

    Returns:
        {'lrc': {'lyric': '...'},          # 原文歌词
         'tlyric': {'lyric': '...'},       # 翻译歌词
         'romalrc': {'lyric': '...'},      # 罗马音歌词
         'code': 200}
    """
    payload = {
        'id': song_id,
        'lv': -1,
        'tv': -1,
        'kv': -1,
    }
    return request_eapi('/api/song/lyric/new', payload)
