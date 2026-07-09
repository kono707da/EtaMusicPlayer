"""元数据批量编辑 + 文件名/路径重命名规则引擎"""
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile  # type: ignore
from mutagen.flac import FLAC  # type: ignore
from mutagen.id3 import (  # type: ignore
    COMM,
    ID3,
    WCOM,
    WCOP,
    WOAF,
    WOAR,
    WOAS,
    WORS,
    WPAY,
    WPUB,
    TALB,
    TBPM,
    TCOM,
    TCON,
    TCOP,
    TDEN,
    TDLY,
    TDOR,
    TDRC,
    TDRL,
    TDTG,
    TENC,
    TEXT,
    TFLT,
    TIPL,
    TIT1,
    TIT2,
    TIT3,
    TKEY,
    TLAN,
    TLEN,
    TMCL,
    TMED,
    TMOO,
    TOAL,
    TOFN,
    TOLY,
    TOPE,
    TOWN,
    TPE1,
    TPE2,
    TPE3,
    TPE4,
    TPOS,
    TPUB,
    TRCK,
    TRSN,
    TRSO,
    TSOA,
    TSOP,
    TSOT,
    TSRC,
    TSSE,
    TSST,
)
from mutagen.mp4 import MP4  # type: ignore
from sqlalchemy.orm import Session

from eta_node.models import Track, WatchDir


logger = logging.getLogger("etamusic.local_node.metadata_editor")

# ==================== 字段定义 ====================

# 数据库表中已有列的字段（这些字段会同时写入数据库 + 文件）
DB_FIELDS: set[str] = {
    "title",
    "artist",
    "album",
    "album_artist",
    "track_no",
    "year",
    "genre",
}

# 整数类型字段（写入时需要类型转换）
INT_FIELDS: set[str] = {"track_no", "year", "disc_no", "bpm", "length", "playlist_delay"}

# 所有可编辑字段（field_key -> field_key，保持字典形式便于 O(1) 查询）
EDITABLE_FIELDS: dict[str, str] = {
    # 数据库存的
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "album_artist",
    "track_no": "track_no",
    "year": "year",
    "genre": "genre",
    # 文件独有
    "subtitle": "subtitle",
    "content_group": "content_group",
    "mood": "mood",
    "set_subtitle": "set_subtitle",
    "original_album": "original_album",
    "original_artist": "original_artist",
    "original_lyricist": "original_lyricist",
    "composer": "composer",
    "conductor": "conductor",
    "remixer": "remixer",
    "lyricist": "lyricist",
    "involved_people": "involved_people",
    "musician_credits": "musician_credits",
    "file_owner": "file_owner",
    "bpm": "bpm",
    "key": "key",
    "isrc": "isrc",
    "language": "language",
    "length": "length",
    "media_type": "media_type",
    "file_type": "file_type",
    "encoder_settings": "encoder_settings",
    "encoded_by": "encoded_by",
    "playlist_delay": "playlist_delay",
    "release_time": "release_time",
    "original_release_time": "original_release_time",
    "encoding_time": "encoding_time",
    "tagging_time": "tagging_time",
    "album_sort": "album_sort",
    "performer_sort": "performer_sort",
    "title_sort": "title_sort",
    "copyright": "copyright",
    "publisher": "publisher",
    "copyright_url": "copyright_url",
    "publisher_url": "publisher_url",
    "commercial_info_url": "commercial_info_url",
    "payment_url": "payment_url",
    "official_audio_file_url": "official_audio_file_url",
    "official_artist_url": "official_artist_url",
    "official_audio_source_url": "official_audio_source_url",
    "internet_radio_station_homepage": "internet_radio_station_homepage",
    "internet_radio_station_name": "internet_radio_station_name",
    "internet_radio_station_owner": "internet_radio_station_owner",
    "comment": "comment",
    "original_filename": "original_filename",
}

# ==================== 格式字段映射 ====================

# MP3 / WAV (ID3 文本 frame，T-frames)
# key -> ID3 Frame class
MP3_TEXT_FRAMES: dict[str, type] = {
    "title": TIT2,
    "artist": TPE1,
    "album": TALB,
    "album_artist": TPE2,
    "genre": TCON,
    "composer": TCOM,
    "conductor": TPE3,
    "remixer": TPE4,
    "lyricist": TEXT,
    "original_artist": TOPE,
    "original_album": TOAL,
    "original_lyricist": TOLY,
    "content_group": TIT1,
    "subtitle": TIT3,
    "set_subtitle": TSST,
    "mood": TMOO,
    "bpm": TBPM,
    "key": TKEY,
    "isrc": TSRC,
    "language": TLAN,
    "length": TLEN,
    "media_type": TMED,
    "file_type": TFLT,
    "encoder_settings": TSSE,
    "encoded_by": TENC,
    "playlist_delay": TDLY,
    "release_time": TDRL,
    "original_release_time": TDOR,
    "encoding_time": TDEN,
    "tagging_time": TDTG,
    "album_sort": TSOA,
    "performer_sort": TSOP,
    "title_sort": TSOT,
    "copyright": TCOP,
    "publisher": TPUB,
    "file_owner": TOWN,
    "original_filename": TOFN,
    "internet_radio_station_name": TRSN,
    "internet_radio_station_owner": TRSO,
    "involved_people": TIPL,
    "musician_credits": TMCL,
}

# MP3 / WAV (ID3 URL frame，W-frames)
# URL frame 用 url 属性而不是 text
MP3_URL_FRAMES: dict[str, type] = {
    "copyright_url": WCOP,
    "publisher_url": WPUB,
    "commercial_info_url": WCOM,
    "payment_url": WPAY,
    "official_audio_file_url": WOAF,
    "official_artist_url": WOAR,
    "official_audio_source_url": WOAS,
    "internet_radio_station_homepage": WORS,
}

# MP3 特殊文本 frame（track_no/year/disc_no 用 "n/total" 格式）
MP3_SPECIAL: dict[str, type] = {
    "track_no": TRCK,
    "year": TDRC,
    "disc_no": TPOS,
}

# FLAC (Vorbis comments) - 支持任意 key，没有对应的用自定义 key
FLAC_KEY_MAP: dict[str, str] = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "albumartist",
    "track_no": "tracknumber",
    "year": "date",
    "genre": "genre",
    "composer": "composer",
    "conductor": "conductor",
    "remixer": "remixer",
    "lyricist": "lyricist",
    "original_artist": "originalartist",
    "original_album": "originalalbum",
    "original_lyricist": "originallyricist",
    "content_group": "grouping",
    "subtitle": "subtitle",
    "set_subtitle": "setsubtitle",
    "mood": "mood",
    "bpm": "bpm",
    "key": "initialkey",
    "isrc": "isrc",
    "language": "language",
    "length": "length",
    "media_type": "mediatype",
    "file_type": "filetype",
    "encoder_settings": "encodersettings",
    "encoded_by": "encodedby",
    "playlist_delay": "playlistdelay",
    "release_time": "releasetime",
    "original_release_time": "originalreleasetime",
    "encoding_time": "encodingtime",
    "tagging_time": "taggingtime",
    "album_sort": "albumsort",
    "performer_sort": "performersort",
    "title_sort": "titlesort",
    "copyright": "copyright",
    "publisher": "publisher",
    "file_owner": "fileowner",
    "original_filename": "originalfilename",
    "internet_radio_station_name": "internetradiostationname",
    "internet_radio_station_owner": "internetradiostationowner",
    "involved_people": "involvedpeople",
    "musician_credits": "musiciancredits",
    "comment": "comment",
    "copyright_url": "copyrighturl",
    "publisher_url": "publisherurl",
    "commercial_info_url": "commercialinfourl",
    "payment_url": "paymenturl",
    "official_audio_file_url": "officialaudiofileurl",
    "official_artist_url": "officialartisturl",
    "official_audio_source_url": "officialaudiosourceurl",
    "internet_radio_station_homepage": "internetradiostationhomepage",
}

# MP4 (atoms) - 只支持有标准 atom 的字段
MP4_KEY_MAP: dict[str, str] = {
    "title": "\xa9nam",
    "artist": "\xa9ART",
    "album": "\xa9alb",
    "album_artist": "aART",
    "year": "\xa9day",
    "genre": "\xa9gen",
    "composer": "\xa9wrt",
    "comment": "\xa9cmt",
    "copyright": "cprt",
    "encoded_by": "\xa9too",
    "content_group": "\xa9grp",
    "encoder_settings": "\xa9too",
}
# MP4 特殊字段（需要特殊格式）
MP4_SPECIAL_TUPLE: dict[str, str] = {"track_no": "trkn", "disc_no": "disk"}
MP4_SPECIAL_INT: dict[str, str] = {"bpm": "tmpo"}

# 重命名模板支持的占位符
TEMPLATE_FIELDS = {"artist", "album", "track_no", "title", "ext"}


def _str_or_empty(v) -> str:
    if v is None:
        return ""
    return str(v)


def _sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = name.strip(". ")
    return name or "_"


def _format_track_no(track_no: Optional[int], width: int = 2) -> str:
    if track_no is None:
        return ""
    return f"{int(track_no):0{width}d}"


def render_template(template: str, track: Track) -> str:
    """根据模板渲染相对路径"""
    ext = (track.ext or "").lower()
    if ext and not ext.startswith("."):
        ext = "." + ext
    values = {
        "artist": _sanitize_filename(_str_or_empty(track.artist) or "UnknownArtist"),
        "album": _sanitize_filename(_str_or_empty(track.album) or "UnknownAlbum"),
        "track_no": _format_track_no(track.track_no),
        "title": _sanitize_filename(_str_or_empty(track.title) or "Untitled"),
        "ext": ext.lstrip("."),
    }

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        fmt = match.group(2)
        if key not in values:
            return match.group(0)
        val = values[key]
        if key == "track_no" and fmt:
            try:
                width = int(fmt.lstrip(":"))
                if track.track_no is not None:
                    return f"{int(track.track_no):0{width}d}"
            except ValueError:
                pass
        return val

    pattern = re.compile(r"\{(\w+)(:[^}]*)?\}")
    rendered = pattern.sub(_replace, template)
    return rendered


# ==================== 文件读取（非 DB 字段） ====================


def _is_id3_tags(mf) -> bool:
    """判断 mf 是否使用 ID3 tags（MP3 / WAV）"""
    if hasattr(mf, "tags") and isinstance(getattr(mf, "tags", None), ID3):
        return True
    return type(mf).__name__ in ("MP3", "WAVE")


def _read_extra_tags_from_file(file_path: str) -> dict[str, str]:
    """从文件读取所有非 DB 字段的当前值。

    返回 {field_key: value_str}，value_str 可能为空字符串。
    """
    extra_fields = [f for f in EDITABLE_FIELDS if f not in DB_FIELDS]
    result: dict[str, str] = {f: "" for f in extra_fields}

    try:
        mf = MutagenFile(file_path)
    except Exception:
        return result
    if mf is None:
        return result

    try:
        tags = getattr(mf, "tags", None)
        if tags is None:
            return result

        if isinstance(mf, FLAC):
            for field, vorbis_key in FLAC_KEY_MAP.items():
                if field in DB_FIELDS:
                    continue
                try:
                    v = tags.get(vorbis_key)
                    if v is None:
                        continue
                    if isinstance(v, list):
                        result[field] = " / ".join(str(x) for x in v) if v else ""
                    else:
                        result[field] = str(v)
                except Exception:
                    pass
        elif isinstance(mf, MP4):
            for field, atom in MP4_KEY_MAP.items():
                if field in DB_FIELDS:
                    continue
                try:
                    v = tags.get(atom)
                    if v is None:
                        continue
                    if isinstance(v, list):
                        result[field] = " / ".join(str(x) for x in v) if v else ""
                    else:
                        result[field] = str(v)
                except Exception:
                    pass
            for field, atom in MP4_SPECIAL_TUPLE.items():
                if field in DB_FIELDS:
                    continue
                try:
                    v = tags.get(atom)
                    if v and isinstance(v, list) and v[0]:
                        result[field] = str(v[0][0])
                except Exception:
                    pass
            for field, atom in MP4_SPECIAL_INT.items():
                if field in DB_FIELDS:
                    continue
                try:
                    v = tags.get(atom)
                    if v and isinstance(v, list) and v[0]:
                        result[field] = str(v[0])
                except Exception:
                    pass
        elif _is_id3_tags(mf):
            # 文本 frame（T-frames）
            for field, frame_cls in MP3_TEXT_FRAMES.items():
                if field in DB_FIELDS:
                    continue
                try:
                    for k in tags.keys():
                        if k.startswith(frame_cls.__name__):
                            v = tags[k]
                            txt = getattr(v, "text", None)
                            if txt is not None:
                                result[field] = " ".join(str(t) for t in txt) if txt else ""
                            else:
                                result[field] = str(v)
                            break
                except Exception:
                    pass
            # URL frame（W-frames）
            for field, frame_cls in MP3_URL_FRAMES.items():
                try:
                    for k in tags.keys():
                        if k.startswith(frame_cls.__name__):
                            v = tags[k]
                            url = getattr(v, "url", None)
                            if url:
                                result[field] = str(url)
                            break
                except Exception:
                    pass
            # 特殊文本 frame（track_no/year/disc_no）
            for field, frame_cls in MP3_SPECIAL.items():
                if field in DB_FIELDS:
                    continue
                try:
                    for k in tags.keys():
                        if k.startswith(frame_cls.__name__):
                            v = tags[k]
                            txt = getattr(v, "text", None)
                            if txt is not None:
                                val_str = " ".join(str(t) for t in txt) if txt else ""
                                if val_str and "/" in val_str:
                                    val_str = val_str.split("/")[0].strip()
                                result[field] = val_str
                            break
                except Exception:
                    pass
            # comment 特殊处理（COMM frame）
            if "comment" not in DB_FIELDS:
                try:
                    for k in tags.keys():
                        if k.startswith("COMM"):
                            v = tags[k]
                            txt = getattr(v, "text", None)
                            if txt is not None:
                                result["comment"] = " ".join(str(t) for t in txt) if txt else ""
                            break
                except Exception:
                    pass
        return result
    finally:
        try:
            mf.close()
        except Exception:
            pass


# ==================== 批量预览 ====================


def batch_preview(db: Session, track_ids: list[int]) -> dict:
    """返回各字段的"公共值或差异标记"看板

    格式: {field: {value: "xxx" | null, is_uniform: bool}}
    null 表示多值不统一。
    """
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    overview: dict = {}

    # 1. DB 字段直接从数据库读
    for f in DB_FIELDS:
        values = [getattr(t, f) for t in tracks]
        unique = set(values)
        if len(unique) <= 1:
            val = values[0] if values else None
            overview[f] = {
                "value": _str_or_empty(val) if val is not None else None,
                "is_uniform": True,
            }
        else:
            overview[f] = {"value": None, "is_uniform": False}

    # 2. 非 DB 字段从文件读
    extra_fields = [f for f in EDITABLE_FIELDS if f not in DB_FIELDS]
    if not tracks:
        for f in extra_fields:
            overview[f] = {"value": None, "is_uniform": True}
        return overview

    if len(tracks) == 1:
        extra_values = _read_extra_tags_from_file(tracks[0].abs_path)
        for f in extra_fields:
            v = extra_values.get(f, "")
            overview[f] = {"value": v if v else None, "is_uniform": True}
    else:
        all_extra: list[dict] = []
        for t in tracks:
            all_extra.append(_read_extra_tags_from_file(t.abs_path))
        for f in extra_fields:
            values = [d.get(f, "") for d in all_extra]
            unique = set(values)
            if len(unique) <= 1:
                val = values[0] if values else ""
                overview[f] = {"value": val if val else None, "is_uniform": True}
            else:
                overview[f] = {"value": None, "is_uniform": False}

    return overview


# ==================== 文件写入 ====================


def _write_tag_to_file(file_path: str, field: str, value: Optional[str]) -> None:
    """用 mutagen 回写文件标签（ID3 / FLAC / MP4）"""
    try:
        mf = MutagenFile(file_path)
    except Exception:
        return
    if mf is None:
        return

    str_val = _str_or_empty(value)

    try:
        if _is_id3_tags(mf):
            _write_mp3(mf, field, str_val)
        elif isinstance(mf, FLAC):
            _write_flac(mf, field, str_val)
        elif isinstance(mf, MP4):
            _write_mp4(mf, field, str_val)
        else:
            # 通用 tags 接口
            try:
                if mf.tags is None:
                    mf.add_tags()
                k = FLAC_KEY_MAP.get(field)
                if k:
                    if str_val:
                        mf.tags[k] = str_val
                    else:
                        mf.tags.pop(k, None)
                    mf.save()
            except Exception:
                pass
    finally:
        try:
            mf.close()
        except Exception:
            pass


def _write_mp3(mf, field: str, value: str) -> None:
    """写入 ID3 tag（MP3 / WAV）"""
    if mf.tags is None:
        mf.add_tags()
    tags = mf.tags

    # 文本 frame（T-frames）
    frame_cls = MP3_TEXT_FRAMES.get(field)
    if frame_cls is not None:
        for k in list(tags.keys()):
            if k.startswith(frame_cls.__name__):
                del tags[k]
        if value:
            # 整数字段验证
            if field in INT_FIELDS:
                try:
                    int(value)
                except ValueError:
                    return
            tags.add(frame_cls(encoding=3, text=value))
        mf.save()
        return

    # URL frame（W-frames）
    url_cls = MP3_URL_FRAMES.get(field)
    if url_cls is not None:
        for k in list(tags.keys()):
            if k.startswith(url_cls.__name__):
                del tags[k]
        if value:
            tags.add(url_cls(url=value))
        mf.save()
        return

    # 特殊文本 frame（track_no/year/disc_no）
    special_cls = MP3_SPECIAL.get(field)
    if special_cls is not None:
        for k in list(tags.keys()):
            if k.startswith(special_cls.__name__):
                del tags[k]
        if value:
            try:
                if field in INT_FIELDS:
                    int(value)
                tags.add(special_cls(encoding=3, text=value))
            except ValueError:
                pass
        mf.save()
        return

    # comment 特殊处理（COMM frame 需要 desc）
    if field == "comment":
        for k in list(tags.keys()):
            if k.startswith("COMM"):
                del tags[k]
        if value:
            tags.add(COMM(encoding=3, lang="eng", desc="", text=value))
        mf.save()
        return

    mf.save()


def _write_flac(mf: FLAC, field: str, value: str) -> None:
    """写入 FLAC Vorbis comment"""
    if mf.tags is None:
        mf.add_tags()
    k = FLAC_KEY_MAP.get(field)
    if not k:
        return
    if value:
        mf.tags[k] = value
    else:
        mf.tags.pop(k, None)
    mf.save()


def _write_mp4(mf: MP4, field: str, value: str) -> None:
    """写入 MP4 atom"""
    if mf.tags is None:
        mf.add_tags()

    atom = MP4_KEY_MAP.get(field)
    if atom is not None:
        if value:
            mf.tags[atom] = value
        else:
            mf.tags.pop(atom, None)
        mf.save()
        return

    tuple_atom = MP4_SPECIAL_TUPLE.get(field)
    if tuple_atom is not None:
        if value:
            try:
                n = int(value)
                mf.tags[tuple_atom] = [(n, 0)]
            except ValueError:
                pass
        else:
            mf.tags.pop(tuple_atom, None)
        mf.save()
        return

    int_atom = MP4_SPECIAL_INT.get(field)
    if int_atom is not None:
        if value:
            try:
                n = int(value)
                mf.tags[int_atom] = [n]
            except ValueError:
                pass
        else:
            mf.tags.pop(int_atom, None)
        mf.save()
        return

    mf.save()


# ==================== 批量更新 ====================


def batch_update_field(
    db: Session, track_ids: list[int], field: str, value: Optional[str]
) -> int:
    """批量写入某字段到 DB + 用 mutagen 回写文件标签。返回更新条数。"""
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"不支持的字段: {field}")

    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    count = 0
    for t in tracks:
        if field in DB_FIELDS:
            if field in INT_FIELDS:
                converted: Optional[int] = None
                if value not in (None, ""):
                    try:
                        converted = int(value)
                    except ValueError:
                        continue
                setattr(t, field, converted)
            else:
                setattr(t, field, value)
        try:
            _write_tag_to_file(t.abs_path, field, value)
        except Exception as e:
            logger.warning("写入文件标签失败 %s 字段 %s: %s", t.abs_path, field, e)
        count += 1
    db.commit()
    return count


def batch_update_multi_fields(
    db: Session, track_ids: list[int], updates: dict[str, Optional[str]]
) -> dict:
    """一次批量写入多个字段到 DB + 回写文件标签。

    updates: {field: value} 字典，field 必须在 EDITABLE_FIELDS 中。
    返回 {"updated": int, "fields": [...], "skipped": [{"field": ..., "reason": ...}]}
    """
    skipped: list[dict] = []
    valid_fields: dict[str, Optional[str]] = {}
    for field, value in updates.items():
        if field not in EDITABLE_FIELDS:
            skipped.append({"field": field, "reason": f"不支持的字段: {field}"})
        else:
            valid_fields[field] = value

    if not valid_fields:
        return {"updated": 0, "fields": [], "skipped": skipped}

    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    count = 0
    for t in tracks:
        for field, value in valid_fields.items():
            if field in DB_FIELDS:
                if field in INT_FIELDS:
                    converted: Optional[int] = None
                    if value not in (None, ""):
                        try:
                            converted = int(value)
                        except ValueError:
                            skipped.append({
                                "field": field,
                                "reason": f"值 '{value}' 不是有效整数，已跳过",
                            })
                            continue
                    setattr(t, field, converted)
                else:
                    setattr(t, field, value)
            try:
                _write_tag_to_file(t.abs_path, field, value)
            except Exception as e:
                skipped.append({"field": field, "reason": f"文件回写失败: {e}"})
        count += 1
    db.commit()
    return {
        "updated": count,
        "fields": list(valid_fields.keys()),
        "skipped": skipped,
    }


# ==================== 重命名 ====================


def rename_preview(
    db: Session, track_ids: list[int], template: str, exceptions: list[int]
) -> list[dict]:
    """预览重命名。exceptions 内的 track_id 跳过。返回 [{track_id, old_path, new_path}]"""
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    items: list[dict] = []
    for t in tracks:
        if t.id in exceptions:
            continue
        new_rel = render_template(template, t)
        items.append(
            {
                "track_id": t.id,
                "old_path": t.rel_path,
                "new_path": new_rel,
            }
        )
    return items


def rename_execute(
    db: Session, track_ids: list[int], template: str, exceptions: list[int]
) -> dict:
    """实际移动文件 + 更新 abs_path/rel_path/filename，事务保护，失败回滚"""
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    success: list[int] = []
    failed: list[dict] = []

    moved_files: list[tuple[Path, Path]] = []  # (src, dst) 用于回滚

    try:
        for t in tracks:
            if t.id in exceptions:
                continue
            wd = db.get(WatchDir, t.watch_dir_id)
            if wd is None:
                failed.append({"track_id": t.id, "error": "未找到监控目录"})
                continue

            new_rel = render_template(template, t)
            root_path = Path(wd.path)
            new_abs = root_path / new_rel
            old_abs = Path(t.abs_path)

            if not old_abs.exists():
                failed.append({"track_id": t.id, "error": "源文件不存在"})
                continue

            if new_abs.exists() and new_abs.resolve() != old_abs.resolve():
                failed.append({"track_id": t.id, "error": "目标路径已存在"})
                continue

            new_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_abs), str(new_abs))
            moved_files.append((old_abs, new_abs))

            t.abs_path = str(new_abs)
            t.rel_path = new_rel
            t.filename = new_abs.name
            ext = new_abs.suffix.lower().lstrip(".")
            t.ext = ext
            success.append(t.id)
        db.commit()
    except Exception as e:
        db.rollback()
        for src, dst in moved_files:
            try:
                if dst.exists() and not src.exists():
                    shutil.move(str(dst), str(src))
            except Exception:
                pass
        return {"success": [], "failed": [{"error": f"事务回滚: {str(e)}"}]}

    return {"success": success, "failed": failed}
