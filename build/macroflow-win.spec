# -*- mode: python ; coding: utf-8 -*-
# macroflow-win.spec
#
# 주요 설정:
#   - onefile: 단일 .exe 파일 (팀 배포용)
#   - DPI Aware 매니페스트 포함 (좌표 어긋남 방지)
#   - UAC: 관리자 권한 불필요 (asInvoker)
#   - UPX 비활성화: 보안 솔루션 오탐 방지

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent   # macro-harness/ 루트

a = Analysis(
    [str(ROOT / 'src' / 'macroflow' / 'main.py')],
    pathex=[str(ROOT / 'src')],
    binaries=[],
    datas=[
        # 필요한 리소스 파일 추가 시 여기에 등록
        # (str(ROOT / 'src' / 'macroflow' / 'assets'), 'assets'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 대형 패키지 제외 → 빌드 크기 최소화
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',
        'unittest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MacroFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # 보안 솔루션 오탐 방지
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI 앱: 콘솔 창 표시 안 함
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # 아이콘 추가 시: icon=str(ROOT / 'assets' / 'icon.ico')
    manifest=str(ROOT / 'build' / 'macroflow.manifest'),  # DPI Aware
    version=None,
    onefile=True,           # 단일 exe
)
