# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


CV_RUNTIME = Path(r'D:\E盘\魔术师\AI魔术师（至尊版）\AI魔术师V7.5（至尊版）\runTime\cvRun310')
CV_BIN = CV_RUNTIME / 'Library' / 'bin'
CV_LIB = CV_RUNTIME / 'Library' / 'lib'

extra_binaries = [
    (str(CV_BIN / 'tcl86t.dll'), '.'),
    (str(CV_BIN / 'tk86t.dll'), '.'),
    (str(CV_BIN / 'libcrypto-3-x64.dll'), '.'),
    (str(CV_BIN / 'libssl-3-x64.dll'), '.'),
    (str(CV_BIN / 'liblzma.dll'), '.'),
    (str(CV_BIN / 'libbz2.dll'), '.'),
]

extra_datas = [
    (str(CV_LIB / 'tcl8.6'), 'tcl8.6'),
    (str(CV_LIB / 'tk8.6'), 'tk8.6'),
    ('assets/app_icon.ico', 'assets'),
]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=extra_datas,
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
    name='极影AI',
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
