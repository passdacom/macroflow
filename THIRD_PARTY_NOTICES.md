# Third-Party Notices

MacroFlow itself is licensed under `GPL-3.0-only`. The official Windows distribution also contains the components below. The checked-in license texts under `licenses/` are copied into every GPL release ZIP.

Locked components: PyQt6 6.11.0; PyQt6-Qt6 6.11.0; PyQt6-sip 13.11.1; Python 3.11.15; OpenSSL 3.5.6; libffi 3.4.6; bzip2 1.0.8; XZ Utils liblzma 5.8.1; python-build-standalone 20260414; PyInstaller 6.19.0.

The SPDX SBOM and provenance record the exact Windows wheels and
python-build-standalone runtime archive that supplied packaged native binaries.

| Component | Locked/release version | License | Included use |
|---|---:|---|---|
| PyQt6 | 6.11.0 | GPL-3.0-only or Riverbank commercial | Python bindings (`QtCore.pyd`, `QtGui.pyd`, `QtWidgets.pyd`) |
| PyQt6-Qt6 | 6.11.0 | Used under LGPL-3.0-only; upstream also offers GPL options | Qt runtime including `Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll` and packaging-selected plugins |
| PyQt6-sip | 13.11.1 | BSD-2-Clause | PyQt support runtime |
| CPython | 3.11.15 | PSF-2.0 and incorporated-component notices | Embedded Python interpreter and standard library |
| OpenSSL | 3.5.6 | Apache-2.0 | `_internal/libcrypto-3-x64.dll` used by CPython's hashing and cryptographic support |
| libffi | 3.4.6 | MIT | `_internal/libffi-8.dll` used by CPython's `ctypes` support |
| bzip2 | 1.0.8 | bzip2-1.0.6 | Statically linked into CPython's packaged `_bz2.pyd` module |
| XZ Utils liblzma | 5.8.1 | 0BSD | Statically linked into CPython's packaged `_lzma.pyd` module; XZ command-line programs are not packaged |
| python-build-standalone | 20260414 | MPL-2.0 | Reproducible CPython build recipes and patches used by `uv python install` |
| PyInstaller | 6.19.0 | GPL-2.0-or-later with Bootloader exception | Builds the executable; the exception permits non-GPL bundles but does not alter dependency licenses |
| Microsoft Visual C++ Runtime / Microsoft Universal C Runtime | build-platform version | Microsoft redistributable terms | Native runtime DLLs selected by the Windows build |

## Source and license locations

Every MacroFlow release produced by the current hardened workflow mirrors the exact MacroFlow commit and reviewed runtime source archives for PyQt6, PyQt6-sip, Qt `qtbase`, Qt `qtsvg`, Qt `qtimageformats`, CPython, OpenSSL, libffi, bzip2, XZ Utils, PyInstaller, and `python-build-standalone`, plus a SHA-256 sidecar for each archive. The generated `SOURCE_CODE.md` identifies the same-release asset URLs and documents equivalent network access under GPLv3 section 6(d). The upstream locations below remain independent verification sources.

- PyQt6: <https://pypi.org/project/PyQt6/6.11.0/>
  Source SHA-256: `45dd60aa69976de1918b5ced6b4e7b6a25abd2a919ecef5fd5826ecc76718889`
- Qt 6.11.0: <https://download.qt.io/archive/qt/6.11/6.11.0/submodules/>
  `qtbase-everywhere-src-6.11.0.tar.xz`: `231ad85979864d914dc9568a1b71c91d6cf20d7b2021d059103bf0eb51cb755e`
  `qtsvg-everywhere-src-6.11.0.tar.xz`: `dfa8d653be07087d9407ed4a4ebae847f8953e0b7abd829f089803ab652a30e6`
  `qtimageformats-everywhere-src-6.11.0.tar.xz`: `d3adb02ac5e2fe24068dbdaee0d7cc68cc3fa8553291c1bfce77c9fe8e940cc8`
- PyQt6-sip: <https://pypi.org/project/PyQt6-sip/13.11.1/>
  Source SHA-256: `869c5b48afe38e55b1ee0dd72182b0886e968cc509b98023ff50010b013ce1be`
- CPython 3.11.15: <https://www.python.org/ftp/python/3.11.15/Python-3.11.15.tar.xz>
  Source SHA-256: `272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625`
- OpenSSL 3.5.6: <https://github.com/openssl/openssl/releases/download/openssl-3.5.6/openssl-3.5.6.tar.gz>
  Source SHA-256: `deae7c80cba99c4b4f940ecadb3c3338b13cb77418409238e57d7f31f2a3b736`
- libffi 3.4.6: <https://github.com/libffi/libffi/releases/download/v3.4.6/libffi-3.4.6.tar.gz>
  Source SHA-256: `b0dea9df23c863a7a50e825440f3ebffabd65df1497108e5d437747843895a4e`
- bzip2 1.0.8: <https://astral-sh.github.io/mirror/files/bzip2-1.0.8.tar.gz>
  Source SHA-256: `ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269`
- XZ Utils 5.8.1: <https://github.com/tukaani-project/xz/releases/download/v5.8.1/xz-5.8.1.tar.gz>
  Source SHA-256: `507825b599356c10dca1cd720c9d0d0c9d5400b9de300af00e4d1ea150795543`
- python-build-standalone 20260414, commit `7af98d60e411de479ab16f5537efc7184dffc25a`: <https://codeload.github.com/astral-sh/python-build-standalone/tar.gz/7af98d60e411de479ab16f5537efc7184dffc25a>
  Source SHA-256: `8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c`
- PyInstaller 6.19.0: <https://pypi.org/project/pyinstaller/6.19.0/>
  Source SHA-256: `ec73aeb8bd9b7f2f1240d328a4542e90b3c6e6fbc106014778431c616592a865`
- Microsoft redistributables: <https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files>

Qt and CPython incorporate additional permissively licensed code. The mirrored source distributions for every packaged Qt module contain their authoritative component-level notices and corresponding third-party sources. The generated PyInstaller inventory and SPDX document identify the exact top-level components of each MacroFlow release.

## No additional restrictions

MacroFlow's own license terms do not add restrictions that conflict with GPLv3 or prevent replacement/debugging of LGPL-covered libraries. Recipients may obtain the complete corresponding MacroFlow source from the exact commit and tag recorded in each release bundle's `SOURCE_CODE.md`.
