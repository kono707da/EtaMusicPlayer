"""网易云 eapi 加密实现

参考 NeteaseCloudMusicApiEnhanced/util/crypto.js 翻译。

eapi 加密：AES-128-ECB + MD5 digest
- 密钥: e82ckenh8dichen8 (16 字节)
- 数据格式: {url}-36cd479b6b5-{json}-36cd479b6b5-{md5}
- 输出: hex 大写

weapi 加密（备用，二维码登录失败时尝试）：AES-128-CBC 双层 + RSA
"""
from __future__ import annotations

import base64
import hashlib
import json
import random

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

# ===== 加密常量 =====
EAPI_KEY = b'e82ckenh8dichen8'  # eapi AES-128-ECB 密钥
WEAPI_PRESET_KEY = b'0CoJUm6Qyw8W8jud'  # weapi 第一层 AES-CBC 密钥
WEAPI_IV = b'0102030405060708'  # weapi AES-CBC IV
LINUXAPI_KEY = b'rFgB&h#%2?^eDg:Q'  # linuxapi AES-128-ECB 密钥

# RSA 公钥（weapi 用，PEM 格式）
WEAPI_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDgtQn2JZ34ZC28NWYpAUd98iZ37BUrX/aKzmFbt7clFSs6sXqHauqKWqdtLkF2KexO40H1YTX8z2lSgBBOAxLsvaklV8k4cBFK9snQXE9/DDaFt6Rr7iVZMldczhC0JNgTz+SHXT6CBHuX3e9SdB1Ua44oncaTWz7OBGLbCiK45wIDAQAB
-----END PUBLIC KEY-----"""

BASE62 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def _aes_ecb_encrypt_hex(plaintext: str, key: bytes) -> str:
    """AES-128-ECB 加密，输出 hex 大写"""
    cipher = AES.new(key, AES.MODE_ECB)
    ct = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    return ct.hex().upper()


def _aes_cbc_encrypt_b64(plaintext: str, key: bytes, iv: bytes) -> str:
    """AES-128-CBC 加密，输出 base64"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    return base64.b64encode(ct).decode('ascii')


def _rsa_encrypt(secret: str) -> str:
    """RSA 加密（无 padding），输出 hex 小写

    weapi 用：secret 反转后用 RSA 公钥加密
    网易云用 RAW (no padding) 模式：直接 modpow(message, e, n)
    """
    pub = RSA.import_key(WEAPI_PUBLIC_KEY_PEM)
    n = pub.n
    e = pub.e
    msg_bytes = secret.encode('utf-8')
    m = int.from_bytes(msg_bytes, 'big')
    c = pow(m, e, n)
    hex_str = format(c, 'x')
    # 补齐到 256 hex (128 字节)
    if len(hex_str) < 256:
        hex_str = '0' * (256 - len(hex_str)) + hex_str
    return hex_str


def eapi_encrypt(url_path: str, payload: dict) -> dict:
    """eapi 加密

    Args:
        url_path: API 完整路径，如 /api/login/qrcode/unikey
        payload: 请求参数 dict

    Returns:
        {'params': '<hex_upper>'}
    """
    text = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    message = f'nobody{url_path}use{text}md5forencrypt'
    digest = hashlib.md5(message.encode('utf-8')).hexdigest()
    data = f'{url_path}-36cd479b6b5-{text}-36cd479b6b5-{digest}'
    return {'params': _aes_ecb_encrypt_hex(data, EAPI_KEY)}


def weapi_encrypt(payload: dict) -> dict:
    """weapi 加密（备用）

    双层 AES-CBC + RSA 加密随机 secret

    Returns:
        {'params': '<b64>', 'encSecKey': '<hex>'}
    """
    text = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    secret = ''.join(random.choices(BASE62, k=16))
    params1 = _aes_cbc_encrypt_b64(text, WEAPI_PRESET_KEY, WEAPI_IV)
    params2 = _aes_cbc_encrypt_b64(params1, secret.encode('utf-8'), WEAPI_IV)
    enc_sec_key = _rsa_encrypt(secret[::-1])  # secret 反转后 RSA 加密
    return {'params': params2, 'encSecKey': enc_sec_key}


def linuxapi_encrypt(payload: dict) -> dict:
    """linuxapi 加密（备用）

    Returns:
        {'eparams': '<hex_upper>'}
    """
    text = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    return {'eparams': _aes_ecb_encrypt_hex(text, LINUXAPI_KEY)}
