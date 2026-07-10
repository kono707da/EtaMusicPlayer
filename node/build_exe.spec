# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for EtaMusic Node standalone exe

Usage:
    cd node
    pyinstaller build_exe.spec

Output: D:/node_release/
"""
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['eta_node/standalone.py'],
    pathex=[],
    binaries=[],
    datas=[
        # config.yaml 随 exe 打包，运行时在 exe 目录下也可覆盖
        ('config.yaml', '.'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.sqlite.pysqlite',
        'mutagen',
        'mutagen.easyid3',
        'mutagen.id3',
        'mutagen.flac',
        'mutagen.oggvorbis',
        'mutagen.mp4',
        'mutagen.asf',
        'mutagen.ogg',
        'mutagen.aac',
        'mutagen.wave',
        'yaml',
        'bcrypt',
        'jose',
        'aiofiles',
        'multipart',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'pdb',
        'ipdb',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='eta_node',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eta_node',
    # 输出到 D:/node_release
    dist_dir='D:/node_release',
)
