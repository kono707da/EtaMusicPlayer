"""音频文件元数据/封面/歌词读写工具

公共模块，供 asmr_one 和 local_node 等插件共用。
支持 MP3 (ID3)、FLAC (Vorbis)、MP4/M4A (iTunes) 格式。
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
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
    USLT,
    WOAS,
)
from mutagen.mp4 import MP4, MP4Cover  # type: ignore

logger = logging.getLogger("etamusic.utils.tag_writer")

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".alac", ".aac", ".wav"}


def write_metadata_to_file(
    file_path: str,
    *,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    album_artist: Optional[str] = None,
    source_url: Optional[str] = None,
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
            _write_flac_tags(mf, title, artist, album, album_artist, source_url)
        elif isinstance(mf, MP4):
            _write_mp4_tags(mf, title, artist, album, album_artist, source_url)
        elif _is_mp3(mf):
            _write_mp3_tags(mf, title, artist, album, album_artist, source_url)
        else:
            _write_generic_tags(mf, title, artist, album, album_artist, source_url)
        mf.save()
        return True
    except Exception as e:
        logger.warning("写入标签失败 %s: %s", file_path, e)
        return False
    finally:
        try:
            mf.close()
        except Exception:
            pass


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
    finally:
        try:
            mf.close()
        except Exception:
            pass


def write_tags_and_cover(
    file_path: str,
    *,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    album_artist: Optional[str] = None,
    source_url: Optional[str] = None,
    cover_bytes: Optional[bytes] = None,
    cover_mime: str = "image/jpeg",
) -> bool:
    """一次性写入元数据 + 封面。

    在 Windows 上 mutagen 直接 save() 原文件时可能出现 "Bad file descriptor" 问题
    （mutagen 的 insert_bytes/resize_file 在某些 Windows 环境下文件描述符异常）。
    本函数使用临时文件策略：在原文件同目录创建临时文件 → 在副本上用 mutagen 写入 → os.replace 替换原文件。
    """
    p = Path(file_path)
    if not p.exists() or p.suffix.lower() not in AUDIO_EXTS:
        return False

    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix=p.suffix,
            prefix=".tmp_",
            dir=str(p.parent),
        )
        os.close(tmp_fd)

        shutil.copy2(str(p), tmp_path)

        mf = MutagenFile(tmp_path)
        if mf is None:
            logger.warning("无法识别音频文件 %s", tmp_path)
            return False

        try:
            if isinstance(mf, FLAC):
                _write_flac_tags(mf, title, artist, album, album_artist, source_url)
            elif isinstance(mf, MP4):
                _write_mp4_tags(mf, title, artist, album, album_artist, source_url)
            elif _is_mp3(mf):
                _write_mp3_tags(mf, title, artist, album, album_artist, source_url)
            else:
                _write_generic_tags(mf, title, artist, album, album_artist, source_url)

            if cover_bytes:
                if isinstance(mf, FLAC):
                    _write_flac_cover(mf, cover_bytes, cover_mime)
                elif isinstance(mf, MP4):
                    _write_mp4_cover(mf, cover_bytes, cover_mime)
                elif _is_mp3(mf):
                    _write_mp3_cover(mf, cover_bytes, cover_mime)

            mf.save()
        finally:
            try:
                mf.close()
            except Exception:
                pass

        os.replace(tmp_path, str(p))
        tmp_path = None
        return True
    except Exception as e:
        logger.warning("写入标签/封面失败 %s: %s", file_path, e)
        return False
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def write_lyrics_to_file(file_path: str, lrc_text: str) -> bool:
    """把 LRC 文本写入音频文件的歌词 tag

    MP3: 写入 ID3 USLT 帧（Unsynchronized lyrics）
    FLAC: 写入 lyrics 字段
    MP4: 写入 ©lyr atom
    其他格式：尝试 tags['lyrics'] 通用接口

    返回是否成功。
    """
    p = Path(file_path)
    if not p.exists() or p.suffix.lower() not in AUDIO_EXTS:
        return False
    if not lrc_text:
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
            if mf.tags is None:
                mf.add_tags()
            mf.tags["lyrics"] = lrc_text
        elif isinstance(mf, MP4):
            if mf.tags is None:
                mf.add_tags()
            mf.tags["\xa9lyr"] = lrc_text
        elif _is_mp3(mf):
            if mf.tags is None:
                mf.add_tags()
            for k in list(mf.tags.keys()):
                if k.startswith("USLT"):
                    del mf.tags[k]
            mf.tags.add(USLT(encoding=3, lang="eng", desc="Lyrics", text=lrc_text))
        else:
            if mf.tags is not None:
                mf.tags["lyrics"] = lrc_text
            else:
                return False
        mf.save()
        return True
    except Exception as e:
        logger.warning("写入歌词失败 %s: %s", file_path, e)
        return False
    finally:
        try:
            mf.close()
        except Exception:
            pass


def vtt_to_lrc(vtt_content: str) -> str:
    """把 WebVTT 字幕转换成 LRC 格式"""
    if not vtt_content:
        return ""

    lines = vtt_content.splitlines()
    lrc_lines: list[str] = []
    time_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})"
    )

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            i += 1
            continue

        m = time_re.match(line)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2))
            ss = int(m.group(3))
            ms = int(m.group(4))
            total_sec = hh * 3600 + mm * 60 + ss + ms / 1000.0
            lrc_min = int(total_sec // 60)
            lrc_sec = total_sec - lrc_min * 60
            timestamp = f"[{lrc_min:02d}:{lrc_sec:05.2f}]"

            i += 1
            text_lines: list[str] = []
            while i < len(lines):
                text_line = lines[i].strip()
                if not text_line:
                    break
                if time_re.match(text_line):
                    break
                text_lines.append(text_line)
                i += 1

            text = " ".join(text_lines).strip()
            if text:
                text = re.sub(r"<[^>]+>", "", text)
                lrc_lines.append(f"{timestamp}{text}")
        else:
            i += 1

    return "\n".join(lrc_lines)


# ===== 内部辅助 =====

def _is_mp3(mf) -> bool:
    if hasattr(mf, "tags") and isinstance(getattr(mf, "tags", None), ID3):
        return True
    return type(mf).__name__ in ("MP3", "WAVE")


def _write_mp3_tags(mf, title, artist, album, album_artist, source_url=None) -> None:
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
    if source_url is not None:
        for k in list(tags.keys()):
            if k == "WOAS":
                del tags[k]
        tags.add(WOAS(url=source_url))


def _write_mp3_cover(mf, image_bytes: bytes, mime: str) -> None:
    if mf.tags is None:
        mf.add_tags()
    tags = mf.tags
    for k in list(tags.keys()):
        if k.startswith("APIC"):
            del tags[k]
    tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=image_bytes))


def _write_flac_tags(mf, title, artist, album, album_artist, source_url=None) -> None:
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
    if source_url is not None:
        mf.tags["website"] = source_url


def _write_flac_cover(mf, image_bytes: bytes, mime: str) -> None:
    mf.clear_pictures()
    pic = Picture()
    pic.data = image_bytes
    pic.type = 3
    pic.mime = mime
    pic.desc = "Cover"
    mf.add_picture(pic)


def _write_mp4_tags(mf, title, artist, album, album_artist, source_url=None) -> None:
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
    if source_url is not None:
        mf.tags["\xa9web"] = source_url


def _write_mp4_cover(mf, image_bytes: bytes, mime: str) -> None:
    if mf.tags is None:
        mf.add_tags()
    fmt = 1 if mime == "image/png" or image_bytes[:4] == b"\x89PNG" else 0
    mf.tags["covr"] = [MP4Cover(image_bytes, imageformat=fmt)]


def _write_generic_tags(mf, title, artist, album, album_artist, source_url=None) -> None:
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
    if source_url is not None:
        mf.tags["website"] = source_url
