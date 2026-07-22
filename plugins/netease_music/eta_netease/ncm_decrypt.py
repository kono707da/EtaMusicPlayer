"""NCM 文件解密

解析网易云音乐 .ncm 加密文件格式，输出原始音频数据 + 元数据。

NCM 格式（参考音乐解锁 DecrypeMusic 逆向）：
1. Magic: "CTENFDAM" (8 bytes)
2. Gap (2 bytes)
3. RC4 Key: 4 bytes len(LE) + encrypted(XOR 0x64 → AES-ECB → skip 17)
4. Metadata: 4 bytes len(LE) + encrypted(XOR 0x63 → skip 22 → base64 → AES-ECB → skip "music:" → JSON)
5. Cover: 5 bytes gap + 4 bytes image_size(LE) + image_data
6. Gap: 13 bytes
7. Audio: XOR with RC4 keystream (256 bytes cycle)

RC4 密钥流生成（非标准 RC4，无 drop-256）：
- KSA: 标准 RC4 密钥调度
- PRGA: 简化版，直接生成 256 字节密钥流
"""
from __future__ import annotations

import io
import json
import logging
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

logger = logging.getLogger("etamusic.plugins.netease.ncm")

# AES 密钥（hex，来自 DecrypeMusic worker.js）
_AES_KEY_CORE = bytes.fromhex("687a4852416d736f356b496e62617857")  # hzHRamso5kInbaxW
_AES_KEY_META = bytes.fromhex("2331346c6a6b5f215c5d2630553c2728")  # #14ljk_!\]&0U<'(

# 魔数: "CTENFDAM" = 0x4E455443 + 0x4D414446 (小端)
_MAGIC_0 = 0x4E455443  # "NETC"
_MAGIC_1 = 0x4D414446  # "MADF"


@dataclass
class NcmResult:
    """NCM 解密结果"""

    audio_data: bytes
    fmt: str  # mp3, flac, etc.
    music_name: str = ""
    artists: list[str] = field(default_factory=list)
    album: str = ""
    album_pic_url: str = ""
    cover_data: Optional[bytes] = None  # 封面图片字节
    bitrate: int = 0


class NcmError(Exception):
    """NCM 解密错误"""


def _aes_ecb_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """AES-ECB 解密 + PKCS7 去填充"""
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(ciphertext)
    try:
        return unpad(decrypted, AES.block_size)
    except ValueError:
        return decrypted


def _build_keystream(key: bytes) -> bytes:
    """生成 RC4 密钥流（256 字节，非标准 RC4）

    KSA: 标准 RC4 密钥调度
    PRGA: 简化版，直接生成 256 字节
    """
    box = list(range(256))
    j = 0
    key_len = len(key)
    for i in range(256):
        j = (box[i] + j + key[i % key_len]) & 0xFF
        box[i], box[j] = box[j], box[i]

    keystream = bytearray(256)
    for i in range(256):
        idx = (i + 1) & 0xFF
        k1 = box[idx]
        k2 = box[(idx + k1) & 0xFF]
        keystream[i] = box[(k1 + k2) & 0xFF]
    return bytes(keystream)


def decrypt_ncm(data: bytes) -> NcmResult:
    """解密 NCM 文件

    Args:
        data: ncm 文件的完整字节

    Returns:
        NcmResult 包含解密后的音频数据和元数据

    Raises:
        NcmError: 文件损坏或格式不支持
    """
    if len(data) < 10:
        raise NcmError("文件过小，非有效 ncm")

    buf = io.BytesIO(data)

    # 1. 魔数检查
    magic = buf.read(8)
    if len(magic) < 8:
        raise NcmError("文件不完整")
    m0, m1 = struct.unpack("<II", magic)
    if m0 != _MAGIC_0 or m1 != _MAGIC_1:
        raise NcmError("ncm 魔数不匹配，文件已损坏或非 ncm 格式")

    # 2. Gap (2 bytes)
    buf.read(2)

    # 3. RC4 Key
    key_len_bytes = buf.read(4)
    if len(key_len_bytes) < 4:
        raise NcmError("读取 RC4 key 长度失败")
    key_len = struct.unpack("<I", key_len_bytes)[0]
    if key_len == 0 or key_len > 1024 * 1024:
        raise NcmError(f"RC4 key 长度异常: {key_len}")

    encrypted_key = buf.read(key_len)
    if len(encrypted_key) < key_len:
        raise NcmError("读取 RC4 key 数据失败")

    # XOR 0x64
    xored_key = bytes(b ^ 0x64 for b in encrypted_key)
    # AES-ECB 解密
    decrypted_key = _aes_ecb_decrypt(xored_key, _AES_KEY_CORE)
    # 跳过前17字节
    rc4_key = decrypted_key[17:]
    if not rc4_key:
        raise NcmError("RC4 key 为空")

    # 生成密钥流
    keystream = _build_keystream(rc4_key)

    # 4. Metadata
    meta_len_bytes = buf.read(4)
    if len(meta_len_bytes) < 4:
        raise NcmError("读取 metadata 长度失败")
    meta_len = struct.unpack("<I", meta_len_bytes)[0]

    metadata = {}
    if meta_len > 0:
        encrypted_meta = buf.read(meta_len)
        if len(encrypted_meta) < meta_len:
            raise NcmError("读取 metadata 数据失败")

        # XOR 0x63
        xored_meta = bytes(b ^ 0x63 for b in encrypted_meta)
        # 跳过前22字节，剩余作为 UTF8 base64 字符串
        if len(xored_meta) > 22:
            b64_str = xored_meta[22:].decode("utf-8", errors="ignore")
            try:
                import base64

                ciphertext_meta = base64.b64decode(b64_str)
                decrypted_meta = _aes_ecb_decrypt(ciphertext_meta, _AES_KEY_META)
                # 跳过前6字符 "music:"
                json_str = decrypted_meta[6:].decode("utf-8", errors="ignore")
                metadata = json.loads(json_str)
            except Exception as e:
                logger.warning("解析 metadata 失败: %s", e)
    else:
        # metadata 长度为0时，已经读取了4字节
        pass

    # 5. Cover image
    cover_data = None
    # 跳过5字节 gap
    buf.read(5)
    image_size_bytes = buf.read(4)
    if len(image_size_bytes) == 4:
        image_size = struct.unpack("<I", image_size_bytes)[0]
        if 0 < image_size < 50 * 1024 * 1024:  # 合理范围（< 50MB）
            cover_data = buf.read(image_size)
            if len(cover_data) < image_size:
                logger.warning("封面图数据不完整")
                cover_data = None
        # 跳过13字节 gap
        buf.read(13)
    else:
        # 没有封面区域，可能是无封面版本
        logger.warning("未找到封面图区域")

    # 6. Audio data
    audio_data = buf.read()
    if not audio_data:
        raise NcmError("无音频数据")

    # XOR 解密
    audio_array = bytearray(audio_data)
    ks_len = len(keystream)
    for i in range(len(audio_array)):
        audio_array[i] ^= keystream[i % ks_len]

    audio_bytes = bytes(audio_array)

    # 确定格式
    fmt = metadata.get("format", "")
    if not fmt:
        # 自动检测
        if audio_bytes[:4] == b"fLaC":
            fmt = "flac"
        elif audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
            fmt = "mp3"
        elif audio_bytes[:4] == b"ftyp":
            fmt = "m4a"
        else:
            fmt = "mp3"
            logger.warning("无法自动检测音频格式，默认 mp3")

    # 提取元数据
    music_name = metadata.get("musicName", "")
    artists_raw = metadata.get("artist", [])
    artists = []
    if isinstance(artists_raw, list):
        for artist_entry in artists_raw:
            if isinstance(artist_entry, list) and artist_entry:
                artists.append(str(artist_entry[0]))
            elif isinstance(artist_entry, str):
                artists.append(artist_entry)

    album = metadata.get("album", "")
    album_pic_url = metadata.get("albumPic", "").replace("http:", "https:")
    bitrate = metadata.get("bitrate", 0) or 0

    return NcmResult(
        audio_data=audio_bytes,
        fmt=fmt,
        music_name=music_name,
        artists=artists,
        album=album,
        album_pic_url=album_pic_url,
        cover_data=cover_data,
        bitrate=bitrate,
    )


def decrypt_ncm_file(file_path: str | Path) -> NcmResult:
    """从文件路径读取并解密 NCM

    Args:
        file_path: ncm 文件路径

    Returns:
        NcmResult
    """
    path = Path(file_path)
    if not path.exists():
        raise NcmError(f"文件不存在: {file_path}")
    data = path.read_bytes()
    return decrypt_ncm(data)
