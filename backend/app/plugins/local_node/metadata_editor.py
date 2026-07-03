"""元数据批量编辑 + 文件名/路径重命名规则引擎"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile  # type: ignore
from mutagen.flac import FLAC  # type: ignore
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TRCK, TDRC, TCON  # type: ignore
from mutagen.mp4 import MP4  # type: ignore
from sqlalchemy.orm import Session

from app.plugins.local_node.models import Track, WatchDir


# 可批量编辑的元数据字段
EDITABLE_FIELDS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "album_artist": "album_artist",
    "track_no": "track_no",
    "year": "year",
    "genre": "genre",
}

# 重命名模板支持的占位符
TEMPLATE_FIELDS = {"artist", "album", "track_no", "title", "ext"}


def _str_or_empty(v) -> str:
    if v is None:
        return ""
    return str(v)


def _sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    # Windows 非法字符
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    # 去除首尾点和空格
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
            # {track_no:02d} 形式
            try:
                width = int(fmt.lstrip(":"))
                if track.track_no is not None:
                    return f"{int(track.track_no):0{width}d}"
            except ValueError:
                pass
        return val

    # 支持 {field} 或 {field:02d}
    pattern = re.compile(r"\{(\w+)(:[^}]*)?\}")
    rendered = pattern.sub(_replace, template)
    return rendered


def batch_preview(db: Session, track_ids: list[int]) -> dict:
    """返回各字段的"公共值或差异标记"看板

    格式: {field: {value: "xxx" | null, is_uniform: bool}}
    null 表示多值不统一。
    """
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    fields = ["title", "artist", "album", "album_artist", "track_no", "year", "genre"]
    overview: dict = {}
    for f in fields:
        values = [getattr(t, f) for t in tracks]
        unique = set(values)
        if len(unique) <= 1:
            val = values[0] if values else None
            overview[f] = {"value": _str_or_empty(val) if val is not None else None, "is_uniform": True}
        else:
            overview[f] = {"value": None, "is_uniform": False}
    return overview


def _write_tag_to_file(file_path: str, field: str, value: Optional[str]) -> None:
    """用 mutagen 回写文件标签（ID3 / FLAC / MP4）"""
    try:
        mf = MutagenFile(file_path)
    except Exception:
        return
    if mf is None:
        return

    str_val = _str_or_empty(value)

    if isinstance(mf, MP3) or (hasattr(mf, "tags") and isinstance(getattr(mf, "tags", None), ID3)):
        _write_mp3(mf, field, str_val)
    elif isinstance(mf, FLAC):
        _write_flac(mf, field, str_val)
    elif isinstance(mf, MP4):
        _write_mp4(mf, field, str_val)
    else:
        # 通用 tags 接口
        try:
            if mf.tags is not None:
                key_map = {
                    "title": "title",
                    "artist": "artist",
                    "album": "album",
                    "album_artist": "albumartist",
                    "track_no": "tracknumber",
                    "year": "date",
                    "genre": "genre",
                }
                k = key_map.get(field)
                if k:
                    mf.tags[k] = str_val
                    mf.save()
        except Exception:
            pass


def _write_mp3(mf: MP3, field: str, value: str) -> None:
    if mf.tags is None:
        mf.add_tags()
    tags = mf.tags
    frame_map = {
        "title": TIT2,
        "artist": TPE1,
        "album": TALB,
        "album_artist": TPE2,
        "genre": TCON,
    }
    if field in frame_map:
        tags.add(frame_map[field](encoding=3, text=value if value else ""))
    elif field == "track_no":
        try:
            tags.add(TRCK(encoding=3, text=str(int(value)) if value else ""))
        except ValueError:
            pass
    elif field == "year":
        try:
            tags.add(TDRC(encoding=3, text=str(int(value)) if value else ""))
        except ValueError:
            pass
    mf.save()


def _write_flac(mf: FLAC, field: str, value: str) -> None:
    key_map = {
        "title": "title",
        "artist": "artist",
        "album": "album",
        "album_artist": "albumartist",
        "track_no": "tracknumber",
        "year": "date",
        "genre": "genre",
    }
    k = key_map.get(field)
    if k:
        if value:
            mf.tags[k] = value
        else:
            mf.tags.pop(k, None)
        mf.save()


def _write_mp4(mf: MP4, field: str, value: str) -> None:
    key_map = {
        "title": "\xa9nam",
        "artist": "\xa9ART",
        "album": "\xa9alb",
        "album_artist": "aART",
        "track_no": "trkn",
        "year": "\xa9day",
        "genre": "\xa9gen",
    }
    k = key_map.get(field)
    if not k:
        return
    if field == "track_no":
        try:
            n = int(value) if value else 0
            mf.tags[k] = [(n, 0)]
        except ValueError:
            pass
    else:
        mf.tags[k] = value if value else ""
    mf.save()


def batch_update_field(
    db: Session, track_ids: list[int], field: str, value: Optional[str]
) -> int:
    """批量写入某字段到 DB + 用 mutagen 回写文件标签。返回更新条数。"""
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"不支持的字段: {field}")

    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    count = 0
    for t in tracks:
        # 类型转换
        if field in ("track_no", "year"):
            converted: Optional[int] = None
            if value not in (None, ""):
                try:
                    converted = int(value)
                except ValueError:
                    continue
            setattr(t, field, converted)
        else:
            setattr(t, field, value)
        # 回写文件
        try:
            _write_tag_to_file(t.abs_path, field, value)
        except Exception:
            pass
        count += 1
    db.commit()
    return count


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

            # 防止目标已存在且非同一文件
            if new_abs.exists() and new_abs.resolve() != old_abs.resolve():
                failed.append({"track_id": t.id, "error": "目标路径已存在"})
                continue

            # 创建目录
            new_abs.parent.mkdir(parents=True, exist_ok=True)
            # 移动文件
            shutil.move(str(old_abs), str(new_abs))
            moved_files.append((old_abs, new_abs))

            # 更新数据库记录
            t.abs_path = str(new_abs)
            t.rel_path = new_rel
            t.filename = new_abs.name
            ext = new_abs.suffix.lower().lstrip(".")
            t.ext = ext
            success.append(t.id)
        db.commit()
    except Exception as e:
        # 回滚：把已移动的文件移回
        db.rollback()
        for src, dst in moved_files:
            try:
                if dst.exists() and not src.exists():
                    shutil.move(str(dst), str(src))
            except Exception:
                pass
        return {"success": [], "failed": [{"error": f"事务回滚: {str(e)}"}]}

    return {"success": success, "failed": failed}
