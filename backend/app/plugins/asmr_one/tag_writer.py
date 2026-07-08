"""兼容层：从公共模块 re-export，保持旧导入路径可用。

新代码请直接使用:
    from app.utils.tag_writer import ...
"""
from app.utils.tag_writer import (  # noqa: F401
    AUDIO_EXTS,
    vtt_to_lrc,
    write_cover_to_file,
    write_lyrics_to_file,
    write_metadata_to_file,
    write_tags_and_cover,
)
