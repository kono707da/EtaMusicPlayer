"""把元数据与封面字节写入音频文件标签（MP3 / FLAC / MP4）

供下载完成后回写标签使用，独立于 local_node.metadata_editor，避免跨插件耦合。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile  # type: ignore
from mutagen.flac import FLAC, Picture  # type: ignore
from mutagen.id3 import (  # type: ignore
    APIC,
    ID3,
    TALB,
    TIT2,
    TPE1,
    TPE2,
)
from mutagen.mp4 import MP4, MP4Cover  # type: ignore

logger = logging.getLogger("etamusic.plugins.asmr_one")

# 支持回写标签的音频扩展名
AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".alac", ".aac"}


def write_metadata_to_file(
    file_path: str,
    *,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    album_artist: Optional[str] = None,
) -> bool:
    """把元数据字段写入音频文件标签。返回是否成功。

    任何字段为 None 时跳过该字段（不覆盖原值）。
    """
    p = Path(file_path)
    if not p.exists() or p.suffix.lower() not in AUDIO_EXTS:
        return False
    try:
        mf = MutagenFile(file_path)
    except Exception as e:
        logger.warning("打开文件失败 %s: %s", file_path, e)
        return False
    if mf is None:
        return False

    try:
        if isinstance(mf, FLAC):
            _write_flac_tags(mf, title, artist, album, album_artist)
        elif isinstance(mf, MP4):
            _write_mp4_tags(mf, title, artist, album, album_artist)
        elif _is_mp3(mf):
            _write_mp3_tags(mf, title, artist, album, album_artist)
        else:
            # 通用 tags 接口兜底
            _write_generic_tags(mf, title, artist, album, album_artist)
        mf.save()
        return True
    except Exception as e:
        logger.warning("写入标签失败 %s: %s", file_path, e)
        return False


def write_cover_to_file(file_path: str, image_bytes: bytes, mime: str = "image/jpeg") -> bool:
    """把封面字节嵌入音频文件。返回是否成功。

    MP3: 添加 APIC 帧（先清掉旧 APIC）
    FLAC: 添加 Picture 对象（先清掉旧 pictures）
    MP4: 写入 covr atom（先清掉旧 covr）
    """
    p = Path(file_path)
    if not p.exists() or p.suffix.lower() not in AUDIO_EXTS:
        return False
    if not image_bytes:
        return False
    try:
        mf = MutagenFile(file_path)
    except Exception as e:
        logger.warning("打开文件失败 %s: %s", file_path, e)
        return False
    if mf is None:
        return False

    try:
        if isinstance(mf, FLAC):
            _write_flac_cover(mf, image_bytes, mime)
        elif isinstance(mf, MP4):
            _write_mp4_cover(mf, image_bytes, mime)
        elif _is_mp3(mf):
            _write_mp3_cover(mf, image_bytes, mime)
        else:
            return False
        mf.save()
        return True
    except Exception as e:
        logger.warning("写入封面失败 %s: %s", file_path, e)
        return False


# ===== 判定 =====

def _is_mp3(mf) -> bool:
    """判断是否为 MP3 文件（含 ID3 tags）"""
    if hasattr(mf, "tags") and isinstance(getattr(mf, "tags", None), ID3):
        return True
    # mutagen.mp3.MP3
    return type(mf).__name__ == "MP3"


# ===== MP3 =====

def _write_mp3_tags(mf, title, artist, album, album_artist) -> None:
    if mf.tags is None:
        mf.add_tags()
    tags = mf.tags
    if title is not None:
        tags.add(TIT2(encoding=3, text=title))
    if artist is not None:
        tags.add(TPE1(encoding=3, text=artist))
    if album is not None:
        tags.add(TALB(encoding=3, text=album))
    if album_artist is not None:
        tags.add(TPE2(encoding=3, text=album_artist))


def _write_mp3_cover(mf, image_bytes: bytes, mime: str) -> None:
    if mf.tags is None:
        mf.add_tags()
    tags = mf.tags
    # 清掉旧 APIC
    for k in list(tags.keys()):
        if k.startswith("APIC"):
            del tags[k]
    tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=image_bytes))


# ===== FLAC =====

def _write_flac_tags(mf, title, artist, album, album_artist) -> None:
    if mf.tags is None:
        mf.add_tags()
    if title is not None:
        mf.tags["title"] = title
    if artist is not None:
        mf.tags["artist"] = artist
    if album is not None:
        mf.tags["album"] = album
    if album_artist is not None:
        mf.tags["albumartist"] = album_artist


def _write_flac_cover(mf, image_bytes: bytes, mime: str) -> None:
    # 清掉旧 picture
    mf.clear_pictures()
    pic = Picture()
    pic.data = image_bytes
    pic.type = 3
    pic.mime = mime
    pic.desc = "Cover"
    mf.add_picture(pic)


# ===== MP4 =====

def _write_mp4_tags(mf, title, artist, album, album_artist) -> None:
    if mf.tags is None:
        mf.add_tags()
    if title is not None:
        mf.tags["\xa9nam"] = title
    if artist is not None:
        mf.tags["\xa9ART"] = artist
    if album is not None:
        mf.tags["\xa9alb"] = album
    if album_artist is not None:
        mf.tags["aART"] = album_artist


def _write_mp4_cover(mf, image_bytes: bytes, mime: str) -> None:
    if mf.tags is None:
        mf.add_tags()
    # MP4 covr 格式：0=jpeg, 1=png
    fmt = 1 if mime == "image/png" or image_bytes[:4] == b"\x89PNG" else 0
    mf.tags["covr"] = [MP4Cover(image_bytes, imageformat=fmt)]


# ===== 通用兜底 =====

def _write_generic_tags(mf, title, artist, album, album_artist) -> None:
    if mf.tags is None:
        return
    key_map = {
        "title": "title",
        "artist": "artist",
        "album": "album",
        "album_artist": "albumartist",
    }
    for field, key in key_map.items():
        val = locals().get(field)
        if val is not None:
            mf.tags[key] = val
