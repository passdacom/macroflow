# Third-Party Notices

MacroFlow itself is licensed under `GPL-3.0-only`. The official Windows distribution also contains the components below. The checked-in license texts under `licenses/` are copied into every GPL release ZIP.

Locked components: PyQt6 6.11.0; PyQt6-Qt6 6.11.0; PyQt6-sip 13.11.1; Python 3.11.15; python-build-standalone 20260414; PyInstaller 6.19.0.

| Component | Locked/release version | License | Included use |
|---|---:|---|---|
| PyQt6 | 6.11.0 | GPL-3.0-only or Riverbank commercial | Python bindings (`QtCore.pyd`, `QtGui.pyd`, `QtWidgets.pyd`) |
| PyQt6-Qt6 | 6.11.0 | LGPL-3.0-only | Qt runtime including `Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll` and packaging-selected plugins |
| PyQt6-sip | 13.11.1 | BSD-2-Clause | PyQt support runtime |
| CPython | 3.11.15 | PSF-2.0 and incorporated-component notices | Embedded Python interpreter and standard library |
| python-build-standalone | 20260414 | MPL-2.0 | Reproducible CPython build recipes and patches used by `uv python install` |
| PyInstaller | 6.19.0 | GPL-2.0-or-later with Bootloader exception | Builds the executable; the exception permits non-GPL bundles but does not alter dependency licenses |
| Microsoft Visual C++ Runtime / UCRT | build-platform version | Microsoft redistributable terms | Native runtime DLLs selected by the Windows build |

## Source and license locations

- PyQt6: <https://pypi.org/project/PyQt6/6.11.0/>
  Source SHA-256: `45dd60aa69976de1918b5ced6b4e7b6a25abd2a919ecef5fd5826ecc76718889`
- Qt 6.11.0: <https://download.qt.io/archive/qt/6.11/6.11.0/submodules/>
  `qtbase-everywhere-src-6.11.0.tar.xz`: `231ad85979864d914dc9568a1b71c91d6cf20d7b2021d059103bf0eb51cb755e`
  `qtsvg-everywhere-src-6.11.0.tar.xz`: `dfa8d653be07087d9407ed4a4ebae847f8953e0b7abd829f089803ab652a30e6`
- PyQt6-sip: <https://pypi.org/project/PyQt6-sip/13.11.1/>
  Source SHA-256: `869c5b48afe38e55b1ee0dd72182b0886e968cc509b98023ff50010b013ce1be`
- CPython 3.11.15: <https://www.python.org/ftp/python/3.11.15/Python-3.11.15.tar.xz>
  Source SHA-256: `272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625`
- python-build-standalone 20260414, commit `7af98d60e411de479ab16f5537efc7184dffc25a`: <https://codeload.github.com/astral-sh/python-build-standalone/tar.gz/7af98d60e411de479ab16f5537efc7184dffc25a>
  Source SHA-256: `8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c`
- PyInstaller 6.19.0: <https://pypi.org/project/pyinstaller/6.19.0/>
  Source SHA-256: `ec73aeb8bd9b7f2f1240d328a4542e90b3c6e6fbc106014778431c616592a865`
- Microsoft redistributables: <https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files>

Qt and CPython incorporate additional permissively licensed code. Their complete source distributions contain the authoritative component-level notices. The generated PyInstaller inventory and SPDX document identify the exact top-level components of each MacroFlow release.

## No additional restrictions

MacroFlow does not impose restrictions that conflict with GPLv3 or prevent replacement/debugging of LGPL-covered libraries. Recipients may obtain the complete corresponding MacroFlow source from the exact commit and tag recorded in each release bundle's `SOURCE_CODE.md`.
