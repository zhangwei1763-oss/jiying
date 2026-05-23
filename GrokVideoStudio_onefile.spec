# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ('assets/app_icon.ico', 'assets'),
]
datas += collect_data_files('faster_whisper')

def collect_tree(source, target):
    collected = []
    if not os.path.isdir(source):
        return collected
    for root, _dirs, files in os.walk(source):
        for filename in files:
            path = os.path.join(root, filename)
            rel = os.path.relpath(root, source)
            dest = target if rel == '.' else os.path.join(target, rel)
            collected.append((path, dest))
    return collected

datas += collect_tree('cuda_runtime', 'cuda_runtime')
datas += collect_tree('tools', 'tools')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GrokVideoStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico',
)
