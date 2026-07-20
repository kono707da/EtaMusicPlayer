"""网易云登录相关 API

实现扫码登录（生成 key、生成二维码 URL、轮询状态）、登录态查询、刷新、
登录成功后账号信息持久化等流程。

参考 NeteaseCloudMusicApiEnhanced 的 module/login_qr_key.js、
login_qr_check.js、login_qr_create.js、login_status.js、login_refresh.js。
"""
from __future__ import annotations

import logging
from typing import Optional

from eta_netease.accounts import save_account
from eta_netease.client import NcmError, check_response, request_eapi

logger = logging.getLogger("etamusic.plugins.netease")


def qrcode_generate_key() -> dict:
    """生成扫码登录用的 unikey

    调用 POST /api/login/qrcode/unikey，payload={'type': 3}。

    Returns:
        {'unikey': 'xxx', 'code': 200}

    Raises:
        NcmError: 接口返回非 200
    """
    j = request_eapi('/api/login/qrcode/unikey', {'type': 3})
    check_response(j, context='生成二维码 key 失败')
    # 部分响应里 unikey 字段也可能叫 key，统一兼容
    unikey = j.get('unikey') or j.get('key')
    if not unikey:
        raise NcmError(j.get('code', -1), '响应缺少 unikey 字段', j)
    return {'unikey': unikey, 'code': j.get('code', 200)}


def qrcode_generate_url(unikey: str) -> dict:
    """根据 unikey 构造二维码扫描 URL

    不调用 API，只本地拼接 URL。

    Args:
        unikey: qrcode_generate_key 返回的 unikey

    Returns:
        {'qrurl': 'https://music.163.com/login?codekey=xxx', 'code': 200}
    """
    qrurl = f'https://music.163.com/login?codekey={unikey}'
    return {'qrurl': qrurl, 'code': 200}


def qrcode_check_status(unikey: str) -> dict:
    """轮询扫码状态

    调用 POST /api/login/qrcode/client/login，payload={'key': unikey, 'type': 3}。
    不调用 check_response，直接返回原始响应，调用方根据 code 判断状态：
      - 800: 二维码过期
      - 801: 等待扫码
      - 802: 已扫码待确认
      - 803: 登录成功（cookie 在 set-cookie 头里，eapi 模式由 client 层处理）
      - 8821: 风控拒绝

    Args:
        unikey: qrcode_generate_key 返回的 unikey

    Returns:
        接口原始响应 dict，包含 code 字段
    """
    j = request_eapi(
        '/api/login/qrcode/client/login',
        {'key': unikey, 'type': 3},
    )
    return j


def login_status(cookies: Optional[dict] = None) -> dict:
    """查询当前登录态与账号信息

    调用 POST /api/w/nuser/account/get，payload={}。
    用于检查 cookie 是否有效，并获取账号详情（昵称、头像、VIP 等）。

    Args:
        cookies: 可选 cookies；None 时 client 自动使用当前账号 cookies

    Returns:
        {'account': {...}, 'profile': {...}, 'code': 200}

    Raises:
        NcmError: 接口返回非 200（如 cookie 失效返回 301）
    """
    j = request_eapi('/api/w/nuser/account/get', {}, cookies=cookies)
    check_response(j, context='查询登录态失败')
    return j


def login_refresh(cookies: Optional[dict] = None) -> dict:
    """刷新登录 token

    调用 POST /api/login/token/refresh，payload={}。

    Args:
        cookies: 可选 cookies；None 时 client 自动使用当前账号 cookies

    Returns:
        {'code': 200} 表示刷新成功

    Raises:
        NcmError: 接口返回非 200
    """
    j = request_eapi('/api/login/token/refresh', {}, cookies=cookies)
    check_response(j, context='刷新登录态失败')
    return j


def handle_login_success(check_response_data: dict,
                         session_cookies: Optional[dict] = None) -> dict:
    """登录成功后处理：查询账号信息并保存

    简化版流程：
      1. 使用 session_cookies 调用 login_status，拿到 account / profile
      2. 提取 ncm_uid、nickname、avatar_url、vip_type
      3. 调用 save_account 持久化
      4. 返回标准账号摘要 dict

    Args:
        check_response_data: qrcode_check_status 返回的 803 响应
            （eapi 模式下 cookie 在 set-cookie 头里，此 dict 仅用于日志/调试，
            实际 cookies 从 session_cookies 取）
        session_cookies: 调用方从 session.cookies 提取的 cookies dict
            （扫码登录成功后必须传入，否则 login_status 会以匿名身份调用）

    Returns:
        {'ncm_uid': ..., 'nickname': ..., 'avatar_url': ..., 'vip_type': ..., 'cookies': ...}

    Raises:
        NcmError: login_status 调用失败或返回数据缺字段
    """
    cookies = session_cookies or {}
    if not cookies:
        logger.warning('handle_login_success 未收到 session_cookies，登录态可能无法持久化')

    # 用刚拿到的 cookies 查询账号信息
    status = login_status(cookies=cookies)
    account = status.get('account') or {}
    profile = status.get('profile') or {}

    ncm_uid = account.get('id') or profile.get('userId')
    if ncm_uid is None:
        raise NcmError(
            status.get('code', -1),
            'login_status 响应缺少账号 id',
            status,
        )

    nickname = profile.get('nickname') or account.get('userName') or str(ncm_uid)
    avatar_url = profile.get('avatarUrl') or ''
    vip_type = profile.get('vipType') or 0

    saved = save_account(
        ncm_uid=str(ncm_uid),
        nickname=nickname,
        avatar_url=avatar_url,
        vip_type=int(vip_type),
        cookies=cookies,
    )

    logger.info(
        '登录成功: %s (uid=%s, vip=%s)',
        nickname, ncm_uid, vip_type,
    )

    return {
        'ncm_uid': str(ncm_uid),
        'nickname': nickname,
        'avatar_url': avatar_url,
        'vip_type': int(vip_type),
        'cookies': saved.get('cookies', cookies),
    }
