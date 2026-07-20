"""网易云 API HTTP 客户端

封装 eapi 加密请求、cookie 处理、错误重试。
所有 API 调用通过 NcmClient 完成。
"""
from __future__ import annotations

import logging
import random
import string
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from eta_netease.accounts import get_current_cookies
from eta_netease.config import (
    API_DOMAIN, DOMAIN, OS_PC, UA_API_PC, UA_WEAPI_PC, VERSION_CODE,
)
from eta_netease.crypto import eapi_encrypt, weapi_encrypt

logger = logging.getLogger("etamusic.plugins.netease")

# 默认超时
DEFAULT_TIMEOUT = 15

# 特殊状态码（NCM 把这些当 200 处理）
SPECIAL_STATUS_CODES = {201, 302, 400, 502, 800, 801, 802, 803}


def _random_nuid() -> str:
    """随机 32 字符 hex（用作 _ntes_nuid / deviceId）"""
    return ''.join(random.choices('0123456789abcdef', k=32))


def _random_wnmcid() -> str:
    """随机 WNMCID 格式：xxxxxx.<ts>.01.0"""
    s = ''.join(random.choices(string.ascii_lowercase, k=6))
    return f'{s}.{int(time.time() * 1000)}.01.0'


def _build_cookie(saved_cookies: dict) -> dict:
    """构建完整 cookie（参照 NeteaseCloudMusicApiEnhanced processCookieObject）"""
    c = dict(saved_cookies or {})
    nuid = c.get('_ntes_nuid') or _random_nuid()
    nnid = c.get('_ntes_nnid') or f'{nuid},{int(time.time() * 1000)}'
    c.update({
        '__remember_me': 'true',
        'ntes_kaola_ad': '1',
        '_ntes_nuid': nuid,
        '_ntes_nnid': nnid,
        'WNMCID': c.get('WNMCID') or _random_wnmcid(),
        'WEVNSM': '1.0.0',
        'osver': OS_PC['osver'],
        'os': OS_PC['os'],
        'channel': OS_PC['channel'],
        'appver': OS_PC['appver'],
        'deviceId': c.get('deviceId') or _random_nuid(),
    })
    return c


def _cookie_to_string(cookie: dict) -> str:
    return '; '.join(f'{k}={v}' for k, v in cookie.items())


def _build_eapi_header(cookie: dict) -> dict:
    """构建 eapi 请求头"""
    return {
        'User-Agent': UA_API_PC,
        'Cookie': _cookie_to_string(cookie),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': DOMAIN,
    }


def _build_eapi_payload(url_path: str, payload: dict, cookie: dict) -> dict:
    """构建 eapi payload（含 header 字段）"""
    eapi_payload = dict(payload)
    eapi_payload['header'] = {
        'osver': OS_PC['osver'],
        'deviceId': cookie.get('deviceId', ''),
        'os': OS_PC['os'],
        'appver': OS_PC['appver'],
        'versioncode': VERSION_CODE,
        'mobilename': '',
        'buildver': str(int(time.time())),
        'resolution': '1920x1080',
        '__csrf': cookie.get('__csrf', ''),
        'channel': OS_PC['channel'],
        'requestId': f'{int(time.time() * 1000)}_{random.randint(0, 9999):04d}',
    }
    return eapi_payload


def make_session() -> requests.Session:
    """创建 session（不读系统代理环境变量）"""
    s = requests.Session()
    s.trust_env = False
    s.proxies = {'http': None, 'https': None}
    # 重试策略
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[502, 503, 504],
        allowed_methods=['GET', 'POST'],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    return s


class NcmError(Exception):
    """网易云 API 错误"""
    def __init__(self, code: int, message: str, data: dict = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f'[{code}] {message}')


# 全局共享 session（减少 TCP 连接开销）
_global_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _global_session
    if _global_session is None:
        _global_session = make_session()
    return _global_session


def request_eapi(url_path: str, payload: dict,
                 cookies: Optional[dict] = None,
                 timeout: int = DEFAULT_TIMEOUT) -> dict:
    """调用 eapi 接口

    Args:
        url_path: /api/xxx 形式
        payload: 请求参数
        cookies: 登录 cookies（None 时用当前账号 + session 中的 cookies）
        timeout: 超时秒数

    Returns:
        解析后的 JSON dict

    Raises:
        NcmError: API 返回错误
        requests.RequestException: 网络错误
    """
    s = _get_session()
    # cookies 优先级：显式传入 > session 中已保存（登录后的 MUSIC_U）> 当前账号
    session_cookies = {c.name: c.value for c in s.cookies}
    if cookies is None:
        cookies = {**get_current_cookies(), **session_cookies}
    full_cookie = _build_cookie(cookies)
    headers = _build_eapi_header(full_cookie)
    eapi_payload = _build_eapi_payload(url_path, payload, full_cookie)

    # URL: /api/xxx → /eapi/xxx
    eapi_path = url_path.replace('/api/', '/eapi/', 1)
    url = f'{API_DOMAIN}{eapi_path}'

    # 加密
    data = eapi_encrypt(url_path, eapi_payload)

    r = s.post(url, headers=headers, data=data, timeout=timeout, verify=False,
               proxies={'http': None, 'https': None})

    # eapi 模式下 cookie 在 set-cookie 头里，requests.Session 会自动保存到 s.cookies
    # 调用方可以通过 _get_session().cookies 获取

    try:
        j = r.json()
    except Exception:
        raise NcmError(r.status_code, f'响应解析失败: {r.text[:200]}')

    code = j.get('code')
    if code is not None:
        j['code'] = int(code)
    return j


def request_weapi(url_path: str, payload: dict,
                  cookies: Optional[dict] = None,
                  timeout: int = DEFAULT_TIMEOUT) -> dict:
    """调用 weapi 接口（备用，目前未使用）"""
    if cookies is None:
        cookies = get_current_cookies()
    full_cookie = _build_cookie(cookies)
    headers = {
        'User-Agent': UA_WEAPI_PC,
        'Cookie': _cookie_to_string(full_cookie),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': DOMAIN,
        'Origin': DOMAIN,
    }
    # weapi: 加 csrf_token
    payload_with_csrf = dict(payload)
    payload_with_csrf['csrf_token'] = full_cookie.get('__csrf', '')

    weapi_path = url_path.replace('/api/', '/weapi/', 1)
    url = f'{DOMAIN}{weapi_path}'
    data = weapi_encrypt(payload_with_csrf)

    s = _get_session()
    r = s.post(url, headers=headers, data=data, timeout=timeout, verify=False,
               proxies={'http': None, 'https': None})

    try:
        return r.json()
    except Exception:
        raise NcmError(r.status_code, f'响应解析失败: {r.text[:200]}')


def request_api_plain(url_path: str, params: dict = None,
                      cookies: Optional[dict] = None,
                      timeout: int = DEFAULT_TIMEOUT) -> dict:
    """调用明文 /api/ 接口（GET）

    部分接口（如歌单详情）可以用明文 GET
    """
    if cookies is None:
        cookies = get_current_cookies()
    full_cookie = _build_cookie(cookies)
    headers = {
        'User-Agent': UA_API_PC,
        'Cookie': _cookie_to_string(full_cookie),
        'Referer': DOMAIN,
    }
    url = f'{API_DOMAIN}{url_path}'
    s = _get_session()
    r = s.get(url, headers=headers, params=params, timeout=timeout, verify=False,
              proxies={'http': None, 'https': None})
    try:
        return r.json()
    except Exception:
        raise NcmError(r.status_code, f'响应解析失败: {r.text[:200]}')


def check_response(j: dict, context: str = '') -> dict:
    """检查响应，非 200 抛 NcmError

    部分接口（如登录轮询）返回 800/801/802/803 是正常业务流程，
    调用方应直接处理 j['code'] 而不调用此函数。
    """
    code = j.get('code')
    if code != 200:
        msg = j.get('message') or j.get('msg') or '未知错误'
        raise NcmError(code, f'{context}: {msg}' if context else msg, j)
    return j
