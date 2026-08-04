#!/usr/bin/env python3
"""Build a self-contained GPL release ZIP for a MacroFlow executable."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import tomllib
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = "3.11.15"
PYTHON_SOURCE_URL = "https://www.python.org/ftp/python/3.11.15/Python-3.11.15.tar.xz"
PYTHON_SOURCE_SHA256 = "272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625"
PYTHON_BUILD_RELEASE = "20260414"
PYTHON_BUILD_SOURCE_COMMIT = "7af98d60e411de479ab16f5537efc7184dffc25a"
PYTHON_BUILD_SOURCE_URL = (
    "https://codeload.github.com/astral-sh/python-build-standalone/tar.gz/"
    + PYTHON_BUILD_SOURCE_COMMIT
)
PYTHON_BUILD_SOURCE_SHA256 = "8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c"
PYQT6_SOURCE_NAME = "pyqt6-6.11.0.tar.gz"
PYQT6_SOURCE_URL = "https://files.pythonhosted.org/packages/8b/47/b25c13eca5bebc6505394d0223e46d7ebf0c57dcac2ed908d7d19b18ab6b/pyqt6-6.11.0.tar.gz"
PYQT6_SOURCE_SHA256 = "45dd60aa69976de1918b5ced6b4e7b6a25abd2a919ecef5fd5826ecc76718889"
QTBASE_SOURCE_NAME = "qtbase-everywhere-src-6.11.0.tar.xz"
QTBASE_SOURCE_URL = "https://download.qt.io/archive/qt/6.11/6.11.0/submodules/qtbase-everywhere-src-6.11.0.tar.xz"
QTBASE_SOURCE_SHA256 = "231ad85979864d914dc9568a1b71c91d6cf20d7b2021d059103bf0eb51cb755e"
QTSVG_SOURCE_NAME = "qtsvg-everywhere-src-6.11.0.tar.xz"
QTSVG_SOURCE_URL = "https://download.qt.io/archive/qt/6.11/6.11.0/submodules/qtsvg-everywhere-src-6.11.0.tar.xz"
QTSVG_SOURCE_SHA256 = "dfa8d653be07087d9407ed4a4ebae847f8953e0b7abd829f089803ab652a30e6"
QTIMAGEFORMATS_SOURCE_NAME = "qtimageformats-everywhere-src-6.11.0.tar.xz"
QTIMAGEFORMATS_SOURCE_URL = "https://download.qt.io/archive/qt/6.11/6.11.0/submodules/qtimageformats-everywhere-src-6.11.0.tar.xz"
QTIMAGEFORMATS_SOURCE_SHA256 = "d3adb02ac5e2fe24068dbdaee0d7cc68cc3fa8553291c1bfce77c9fe8e940cc8"
OPENSSL_SOURCE_NAME = "openssl-3.5.6.tar.gz"
OPENSSL_SOURCE_URL = (
    "https://github.com/openssl/openssl/releases/download/openssl-3.5.6/openssl-3.5.6.tar.gz"
)
OPENSSL_SOURCE_SHA256 = "deae7c80cba99c4b4f940ecadb3c3338b13cb77418409238e57d7f31f2a3b736"
LIBFFI_SOURCE_NAME = "libffi-3.4.6.tar.gz"
LIBFFI_SOURCE_URL = (
    "https://github.com/libffi/libffi/releases/download/v3.4.6/libffi-3.4.6.tar.gz"
)
LIBFFI_SOURCE_SHA256 = "b0dea9df23c863a7a50e825440f3ebffabd65df1497108e5d437747843895a4e"
BZIP2_SOURCE_NAME = "bzip2-1.0.8.tar.gz"
BZIP2_SOURCE_URL = "https://astral-sh.github.io/mirror/files/bzip2-1.0.8.tar.gz"
BZIP2_SOURCE_SHA256 = "ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269"
XZ_SOURCE_NAME = "xz-5.8.1.tar.gz"
XZ_SOURCE_URL = "https://github.com/tukaani-project/xz/releases/download/v5.8.1/xz-5.8.1.tar.gz"
XZ_SOURCE_SHA256 = "507825b599356c10dca1cd720c9d0d0c9d5400b9de300af00e4d1ea150795543"
PYQT6_SIP_SOURCE_NAME = "pyqt6_sip-13.11.1.tar.gz"
PYQT6_SIP_SOURCE_URL = "https://files.pythonhosted.org/packages/90/24/a753e1af94b9ae5b2da63d4598457308da3cdbf0838c959381db086ccc86/pyqt6_sip-13.11.1.tar.gz"
PYQT6_SIP_SOURCE_SHA256 = "869c5b48afe38e55b1ee0dd72182b0886e968cc509b98023ff50010b013ce1be"
PYINSTALLER_SOURCE_NAME = "pyinstaller-6.19.0.tar.gz"
PYINSTALLER_SOURCE_URL = "https://files.pythonhosted.org/packages/c8/63/fd62472b6371d89dc138d40c36d87a50dc2de18a035803bbdc376b4ffac4/pyinstaller-6.19.0.tar.gz"
PYINSTALLER_SOURCE_SHA256 = "ec73aeb8bd9b7f2f1240d328a4542e90b3c6e6fbc106014778431c616592a865"
PYQT6_WINDOWS_WHEEL_URL = "https://files.pythonhosted.org/packages/6f/85/dd9f03d78d87460e109e0121cd6201c5802bdd655656bf2780e964870fea/pyqt6-6.11.0-cp310-abi3-win_amd64.whl"
PYQT6_WINDOWS_WHEEL_SHA256 = "bd11b459c54dca068e988a42cf838303334f0d441b9d16d92ae6719fcb5ac6ba"
PYQT6_QT6_WINDOWS_WHEEL_URL = "https://files.pythonhosted.org/packages/36/cd/da0147d331b44587a7214c7f59719ac4f8e9433b268016962b02067007d1/pyqt6_qt6-6.11.0-py3-none-win_amd64.whl"
PYQT6_QT6_WINDOWS_WHEEL_SHA256 = "b0e42629cef2575f2178aaeb32b0e539291df869f91f4df48983da3ccaad05af"
PYQT6_SIP_WINDOWS_WHEEL_URL = "https://files.pythonhosted.org/packages/4a/d6/c40e8ae38a6e2bce9e837b64688f55746bfdad1aa557eb733fb5e90edd7c/pyqt6_sip-13.11.1-cp311-cp311-win_amd64.whl"
PYQT6_SIP_WINDOWS_WHEEL_SHA256 = "98db8ed37cf08130e1ee74b8ff47a6bfb8c3cdfe826310597a630a50e47feedc"
PYINSTALLER_WINDOWS_WHEEL_URL = "https://files.pythonhosted.org/packages/9c/d3/6d5e62b8270e2b53a6065e281b3a7785079b00e9019c8019952828dd1669/pyinstaller-6.19.0-py3-none-win_amd64.whl"
PYINSTALLER_WINDOWS_WHEEL_SHA256 = "b5bb6536c6560330d364d91522250f254b107cf69129d9cbcd0e6727c570be33"
PYTHON_WINDOWS_RUNTIME_URL = "https://github.com/astral-sh/python-build-standalone/releases/download/20260414/cpython-3.11.15%2B20260414-x86_64-pc-windows-msvc-install_only_stripped.tar.gz"
PYTHON_WINDOWS_RUNTIME_SHA256 = "71ffdf290e0483f0881e02518ecb9cedb449807856ae7dc76aa630e5acd00919"
PYTHON_WINDOWS_RUNTIME_KEY = "cpython-3.11.15-windows-x86_64-none"
COMPANION_SOURCE_ASSETS = (
    (PYQT6_SOURCE_NAME, PYQT6_SOURCE_URL, PYQT6_SOURCE_SHA256),
    (QTBASE_SOURCE_NAME, QTBASE_SOURCE_URL, QTBASE_SOURCE_SHA256),
    (QTSVG_SOURCE_NAME, QTSVG_SOURCE_URL, QTSVG_SOURCE_SHA256),
    (
        QTIMAGEFORMATS_SOURCE_NAME,
        QTIMAGEFORMATS_SOURCE_URL,
        QTIMAGEFORMATS_SOURCE_SHA256,
    ),
    (OPENSSL_SOURCE_NAME, OPENSSL_SOURCE_URL, OPENSSL_SOURCE_SHA256),
    (LIBFFI_SOURCE_NAME, LIBFFI_SOURCE_URL, LIBFFI_SOURCE_SHA256),
    (BZIP2_SOURCE_NAME, BZIP2_SOURCE_URL, BZIP2_SOURCE_SHA256),
    (XZ_SOURCE_NAME, XZ_SOURCE_URL, XZ_SOURCE_SHA256),
    (f"Python-{PYTHON_VERSION}.tar.xz", PYTHON_SOURCE_URL, PYTHON_SOURCE_SHA256),
    (PYQT6_SIP_SOURCE_NAME, PYQT6_SIP_SOURCE_URL, PYQT6_SIP_SOURCE_SHA256),
    (PYINSTALLER_SOURCE_NAME, PYINSTALLER_SOURCE_URL, PYINSTALLER_SOURCE_SHA256),
    (
        f"python-build-standalone-{PYTHON_BUILD_RELEASE}-{PYTHON_BUILD_SOURCE_COMMIT}.tar.gz",
        PYTHON_BUILD_SOURCE_URL,
        PYTHON_BUILD_SOURCE_SHA256,
    ),
)
LICENSE_FILES = (
    "GPL-3.0-only.txt",
    "LGPL-3.0-only.txt",
    "BSD-2-Clause-PyQt6-sip.txt",
    "PSF-2.0-Python.txt",
    "MPL-2.0-python-build-standalone.txt",
    "OpenSSL-3-Apache-2.0.txt",
    "libffi-MIT.txt",
    "bzip2-1.0.8.txt",
    "liblzma-0BSD.txt",
    "PyInstaller-COPYING.txt",
)
STATIC_FILES = (
    "LICENSE",
    "COPYRIGHT",
    "README.md",
    "BUILDING.md",
    "THIRD_PARTY_NOTICES.md",
)
PACKAGE_LICENSES = {
    "macroflow": "GPL-3.0-only",
    "pyqt6": "GPL-3.0-only",
    "pyqt6-qt6": "LGPL-3.0-only",
    "pyqt6-sip": "BSD-2-Clause",
    "pyinstaller": "GPL-2.0-or-later WITH Bootloader-exception",
}
PACKAGE_DISPLAY_NAMES = {
    "macroflow": "MacroFlow",
    "pyqt6": "PyQt6",
    "pyqt6-qt6": "PyQt6-Qt6",
    "pyqt6-sip": "PyQt6-sip",
    "pyinstaller": "PyInstaller",
}
LOCKED_PACKAGE_VERSIONS = {
    "macroflow": "1.9.0",
    "pyqt6": "6.11.0",
    "pyqt6-qt6": "6.11.0",
    "pyqt6-sip": "13.11.1",
    "pyinstaller": "6.19.0",
}
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_full_sha(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("commit must be a 40-character lowercase Git SHA")
    return value


def _validate_repository(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value) is None:
        raise ValueError("repository must use owner/name form")
    return value


def _validate_tag(value: str) -> str:
    if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+-build[0-9]+", value) is None:
        raise ValueError("tag must use vX.Y.Z-buildN form")
    return value


def _validate_release_identity(
    *, exe_name: str, tag: str, run_number: str, project_version: str
) -> None:
    exe_match = re.fullmatch(
        r"MacroFlow-v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)-build(?P<build>[0-9]+)\.exe",
        exe_name,
    )
    tag_match = re.fullmatch(
        r"v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)-build(?P<build>[0-9]+)", tag
    )
    if exe_match is None or tag_match is None or re.fullmatch(r"[0-9]+", run_number) is None:
        raise ValueError("project, executable, tag, and run number versions must match")
    versions = {project_version, exe_match.group("version"), tag_match.group("version")}
    builds = {run_number, exe_match.group("build"), tag_match.group("build")}
    if len(versions) != 1 or len(builds) != 1:
        raise ValueError("project, executable, tag, and run number versions must match")


def _locked_packages() -> dict[str, dict[str, Any]]:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = {package["name"]: package for package in lock["package"]}
    missing = PACKAGE_LICENSES.keys() - packages.keys()
    if missing:
        raise ValueError(f"uv.lock is missing required packages: {sorted(missing)}")
    mismatches = {
        name: str(packages[name]["version"])
        for name, expected in LOCKED_PACKAGE_VERSIONS.items()
        if str(packages[name]["version"]) != expected
    }
    if mismatches:
        raise ValueError(f"uv.lock versions differ from reviewed release sources: {mismatches}")

    reviewed_wheels = {
        "pyqt6": (PYQT6_WINDOWS_WHEEL_URL, PYQT6_WINDOWS_WHEEL_SHA256),
        "pyqt6-qt6": (PYQT6_QT6_WINDOWS_WHEEL_URL, PYQT6_QT6_WINDOWS_WHEEL_SHA256),
        "pyqt6-sip": (PYQT6_SIP_WINDOWS_WHEEL_URL, PYQT6_SIP_WINDOWS_WHEEL_SHA256),
        "pyinstaller": (PYINSTALLER_WINDOWS_WHEEL_URL, PYINSTALLER_WINDOWS_WHEEL_SHA256),
    }
    for name, (url, digest) in reviewed_wheels.items():
        wheel = next(
            (
                item
                for item in packages[name].get("wheels", [])
                if item.get("url") == url and item.get("hash") == f"sha256:{digest}"
            ),
            None,
        )
        if wheel is None:
            raise ValueError(f"uv.lock is missing reviewed Windows wheel provenance for {name}")

    manifest = json.loads((ROOT / "build" / "python-downloads.json").read_text(encoding="utf-8"))
    runtime = manifest.get(PYTHON_WINDOWS_RUNTIME_KEY)
    if not isinstance(runtime, dict) or runtime.get("url") != PYTHON_WINDOWS_RUNTIME_URL:
        raise ValueError("Windows Python runtime manifest URL differs from the reviewed artifact")
    if runtime.get("sha256") != PYTHON_WINDOWS_RUNTIME_SHA256:
        raise ValueError("Windows Python runtime manifest checksum differs from the reviewed artifact")
    if runtime.get("build") != PYTHON_BUILD_RELEASE:
        raise ValueError("Windows Python runtime manifest build differs from the reviewed release")
    return packages


def _verify_python_build_release() -> None:
    base_executable = Path(getattr(sys, "_base_executable", sys.executable)).resolve()
    candidates = (base_executable.parent / "BUILD", base_executable.parent.parent / "BUILD")
    build_file = next((path for path in candidates if path.is_file()), None)
    if build_file is None or build_file.read_text(encoding="ascii").strip() != PYTHON_BUILD_RELEASE:
        raise ValueError(
            f"release bundle requires python-build-standalone release {PYTHON_BUILD_RELEASE}"
        )


def _source_code_markdown(
    *, repository: str, commit: str, tag: str, packages: dict[str, dict[str, Any]]
) -> str:
    lines = [
        "# Corresponding Source",
        "",
        "This binary is distributed under GNU GPLv3. Its exact MacroFlow source, build scripts,",
        "locked dependency graph, and installation instructions are available at:",
        "",
        f"- Commit: `{commit}`",
        f"- Tag: `{tag}`",
        f"- Source tree: https://github.com/{repository}/tree/{commit}",
        f"- Source archive (ZIP): https://github.com/{repository}/archive/{commit}.zip",
        f"- Source archive (tar.gz): https://github.com/{repository}/archive/{commit}.tar.gz",
        f"- Same-release source asset: https://github.com/{repository}/releases/download/{tag}/MacroFlow-{tag}-source.tar.gz",
        f"- Source checksum sidecar: https://github.com/{repository}/releases/download/{tag}/MacroFlow-{tag}-source.tar.gz.sha256",
        "",
        "The complete build procedure is in `BUILDING.md`.",
        "",
        "## Same-release companion source assets",
        "",
        "The exact reviewed runtime source archives below are attached to the same GitHub Release",
        f"at https://github.com/{repository}/releases/tag/{tag}, with no access charge:",
        "",
    ]
    for name, upstream_url, digest in COMPANION_SOURCE_ASSETS:
        lines.extend(
            [
                f"- `{name}`",
                f"  - Release asset: https://github.com/{repository}/releases/download/{tag}/{name}",
                f"  - Checksum sidecar: https://github.com/{repository}/releases/download/{tag}/{name}.sha256",
                f"  - SHA-256: `{digest}`",
                f"  - Upstream source: {upstream_url}",
            ]
        )
    lines.extend(
        [
            "",
            "## Equivalent network access and additional source locations",
            "",
            "The object code and corresponding source are provided from the same GitHub Release",
            "without charge under GPLv3 section 6(d). The distributor must stop distributing this",
            "binary if equivalent source access cannot be maintained.",
            "",
            "The following upstream locations provide independently verifiable copies:",
            "",
        ]
    )
    for name in ("pyqt6", "pyqt6-sip", "pyinstaller"):
        package = packages[name]
        sdist = package.get("sdist")
        if not isinstance(sdist, dict):
            raise ValueError(f"uv.lock package {name} has no source distribution")
        lines.extend(
            [
                f"- {PACKAGE_DISPLAY_NAMES[name]} {package['version']}: {sdist['url']}",
                f"  - {sdist['hash']}",
            ]
        )
    lines.extend(
        [
            "- Qt 6.11.0 source modules: https://download.qt.io/archive/qt/6.11/6.11.0/submodules/",
            "  - qtbase SHA-256: `231ad85979864d914dc9568a1b71c91d6cf20d7b2021d059103bf0eb51cb755e`",
            "  - qtsvg SHA-256: `dfa8d653be07087d9407ed4a4ebae847f8953e0b7abd829f089803ab652a30e6`",
            "  - qtimageformats SHA-256: `d3adb02ac5e2fe24068dbdaee0d7cc68cc3fa8553291c1bfce77c9fe8e940cc8`",
            f"- CPython {PYTHON_VERSION}: {PYTHON_SOURCE_URL}",
            f"  - sha256:{PYTHON_SOURCE_SHA256}",
            f"- python-build-standalone build recipes release {PYTHON_BUILD_RELEASE}",
            f"  - Commit: `{PYTHON_BUILD_SOURCE_COMMIT}`",
            f"  - Source archive: {PYTHON_BUILD_SOURCE_URL}",
            f"  - sha256:{PYTHON_BUILD_SOURCE_SHA256}",
            "",
            "If any listed source becomes unavailable, open an issue at the repository URL above.",
            "No fee is charged for source access.",
            "",
        ]
    )
    return "\n".join(lines)


def _spdx_document(
    *,
    repository: str,
    commit: str,
    tag: str,
    exe_name: str,
    exe_hash: str,
    packages: dict[str, dict[str, Any]],
    source_date_epoch: int,
) -> dict[str, Any]:
    created = datetime.fromtimestamp(source_date_epoch, UTC).isoformat().replace("+00:00", "Z")
    spdx_packages: list[dict[str, Any]] = []
    for name in ("macroflow", "pyqt6", "pyqt6-qt6", "pyqt6-sip"):
        package = packages[name]
        display = PACKAGE_DISPLAY_NAMES[name]
        version = str(package["version"])
        source = package.get("sdist", {}).get("url", "NOASSERTION")
        item: dict[str, Any] = {
            "name": display,
            "SPDXID": f"SPDXRef-Package-{re.sub(r'[^A-Za-z0-9.-]', '-', display)}",
            "versionInfo": version,
            "downloadLocation": source,
            "filesAnalyzed": False,
            "licenseConcluded": PACKAGE_LICENSES[name],
            "licenseDeclared": PACKAGE_LICENSES[name],
            "copyrightText": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": f"pkg:pypi/{name}@{version}",
                }
            ],
        }
        source_hash = package.get("sdist", {}).get("hash", "")
        if isinstance(source_hash, str) and source_hash.startswith("sha256:"):
            item["checksums"] = [
                {"algorithm": "SHA256", "checksumValue": source_hash.removeprefix("sha256:")}
            ]
        if name == "pyqt6-qt6":
            item["licenseConcluded"] = "NOASSERTION"
            item["licenseDeclared"] = "NOASSERTION"
            item["licenseComments"] = (
                "Qt modules are used under LGPL-3.0-only; the binary distribution also "
                "contains separately licensed third-party code documented by Qt."
            )
        if name == "macroflow":
            item["downloadLocation"] = f"https://github.com/{repository}/tree/{commit}"
        spdx_packages.append(item)

    spdx_packages.extend(
        [
            {
                "name": "PyQt6 Windows wheel",
                "SPDXID": "SPDXRef-Package-PyQt6-Windows-Wheel",
                "versionInfo": "6.11.0",
                "downloadLocation": PYQT6_WINDOWS_WHEEL_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": PYQT6_WINDOWS_WHEEL_SHA256}
                ],
                "licenseConcluded": "GPL-3.0-only",
                "licenseDeclared": "GPL-3.0-only",
                "copyrightText": "Copyright Riverbank Computing Limited",
            },
            {
                "name": "PyQt6-Qt6 Windows wheel",
                "SPDXID": "SPDXRef-Package-PyQt6-Qt6-Windows-Wheel",
                "versionInfo": "6.11.0",
                "downloadLocation": PYQT6_QT6_WINDOWS_WHEEL_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": PYQT6_QT6_WINDOWS_WHEEL_SHA256,
                    }
                ],
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "licenseComments": "Binary origin for the packaged Qt runtime; component licenses are documented by the reviewed Qt source modules and notices.",
                "copyrightText": "Copyright The Qt Company Ltd. and other contributors",
            },
            {
                "name": "PyQt6-sip Windows wheel",
                "SPDXID": "SPDXRef-Package-PyQt6-sip-Windows-Wheel",
                "versionInfo": "13.11.1",
                "downloadLocation": PYQT6_SIP_WINDOWS_WHEEL_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": PYQT6_SIP_WINDOWS_WHEEL_SHA256,
                    }
                ],
                "licenseConcluded": "BSD-2-Clause",
                "licenseDeclared": "BSD-2-Clause",
                "copyrightText": "Copyright Riverbank Computing Limited",
            },
            {
                "name": "PyInstaller Windows wheel",
                "SPDXID": "SPDXRef-Package-PyInstaller-Windows-Wheel",
                "versionInfo": "6.19.0",
                "downloadLocation": PYINSTALLER_WINDOWS_WHEEL_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": PYINSTALLER_WINDOWS_WHEEL_SHA256,
                    }
                ],
                "licenseConcluded": "GPL-2.0-or-later WITH Bootloader-exception",
                "licenseDeclared": "GPL-2.0-or-later WITH Bootloader-exception",
                "copyrightText": "NOASSERTION",
            },
            {
                "name": "python-build-standalone Windows runtime",
                "SPDXID": "SPDXRef-Package-python-build-standalone-Windows-Runtime",
                "versionInfo": f"{PYTHON_VERSION}+{PYTHON_BUILD_RELEASE}",
                "downloadLocation": PYTHON_WINDOWS_RUNTIME_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": PYTHON_WINDOWS_RUNTIME_SHA256,
                    }
                ],
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "licenseComments": "Binary origin for the packaged CPython runtime; component licenses and exact source archives are recorded separately.",
                "copyrightText": "NOASSERTION",
            },
            {
                "name": "Qt Base",
                "SPDXID": "SPDXRef-Package-Qt-Base",
                "versionInfo": "6.11.0",
                "downloadLocation": QTBASE_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": QTBASE_SOURCE_SHA256}
                ],
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "licenseComments": "Qt code is used under LGPL-3.0-only; bundled third-party code has separate licenses in the source archive.",
                "copyrightText": "Copyright The Qt Company Ltd. and other contributors",
            },
            {
                "name": "Qt SVG",
                "SPDXID": "SPDXRef-Package-Qt-SVG",
                "versionInfo": "6.11.0",
                "downloadLocation": QTSVG_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": QTSVG_SOURCE_SHA256}
                ],
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "licenseComments": "Qt code is used under LGPL-3.0-only; bundled third-party code has separate licenses in the source archive.",
                "copyrightText": "Copyright The Qt Company Ltd. and other contributors",
            },
            {
                "name": "Qt Image Formats",
                "SPDXID": "SPDXRef-Package-Qt-Image-Formats",
                "versionInfo": "6.11.0",
                "downloadLocation": QTIMAGEFORMATS_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": QTIMAGEFORMATS_SOURCE_SHA256,
                    }
                ],
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "licenseComments": "Qt code is used under LGPL-3.0-only; image codecs include separately licensed third-party code documented in the source archive.",
                "copyrightText": "Copyright The Qt Company Ltd. and other contributors",
            },
            {
                "name": "OpenSSL",
                "SPDXID": "SPDXRef-Package-OpenSSL",
                "versionInfo": "3.5.6",
                "downloadLocation": OPENSSL_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": OPENSSL_SOURCE_SHA256}
                ],
                "licenseConcluded": "Apache-2.0",
                "licenseDeclared": "Apache-2.0",
                "copyrightText": "Copyright The OpenSSL Project Authors",
            },
            {
                "name": "libffi",
                "SPDXID": "SPDXRef-Package-libffi",
                "versionInfo": "3.4.6",
                "downloadLocation": LIBFFI_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": LIBFFI_SOURCE_SHA256}
                ],
                "licenseConcluded": "MIT",
                "licenseDeclared": "MIT",
                "copyrightText": "Copyright Anthony Green, Red Hat, Inc. and other contributors",
            },
            {
                "name": "bzip2",
                "SPDXID": "SPDXRef-Package-bzip2",
                "versionInfo": "1.0.8",
                "downloadLocation": BZIP2_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": BZIP2_SOURCE_SHA256}
                ],
                "licenseConcluded": "bzip2-1.0.6",
                "licenseDeclared": "bzip2-1.0.6",
                "copyrightText": "Copyright (C) 1996-2019 Julian R Seward",
            },
            {
                "name": "XZ Utils liblzma",
                "SPDXID": "SPDXRef-Package-XZ-liblzma",
                "versionInfo": "5.8.1",
                "downloadLocation": XZ_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": XZ_SOURCE_SHA256}
                ],
                "licenseConcluded": "0BSD",
                "licenseDeclared": "0BSD",
                "licenseComments": "Only liblzma is statically linked into CPython's _lzma.pyd; other XZ Utils programs are not packaged.",
                "copyrightText": "Copyright The XZ Utils authors and contributors",
            },
            {
                "name": "MacroFlow Windows Distribution",
                "SPDXID": "SPDXRef-Package-MacroFlow-Binary",
                "versionInfo": str(packages["macroflow"]["version"]),
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "checksums": [{"algorithm": "SHA256", "checksumValue": exe_hash}],
                "licenseConcluded": "GPL-3.0-only",
                "licenseDeclared": "GPL-3.0-only",
                "copyrightText": "Copyright (C) 2026 Han Phillip",
            },
            {
                "name": "PyInstaller Bootloader",
                "SPDXID": "SPDXRef-Package-PyInstaller-Bootloader",
                "versionInfo": str(packages["pyinstaller"]["version"]),
                "downloadLocation": PYINSTALLER_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": PYINSTALLER_SOURCE_SHA256}
                ],
                "licenseConcluded": "GPL-2.0-or-later WITH Bootloader-exception",
                "licenseDeclared": "GPL-2.0-or-later WITH Bootloader-exception",
                "licenseComments": "PyInstaller bootloader exception text is included in licenses/PyInstaller-COPYING.txt.",
                "copyrightText": "NOASSERTION",
            },
            {
                "name": "Python",
                "SPDXID": "SPDXRef-Package-Python",
                "versionInfo": PYTHON_VERSION,
                "downloadLocation": PYTHON_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": PYTHON_SOURCE_SHA256}
                ],
                "licenseConcluded": "PSF-2.0",
                "licenseDeclared": "PSF-2.0",
                "copyrightText": "Copyright Python Software Foundation and contributors",
            },
            {
                "name": "Microsoft Visual C++ Runtime",
                "SPDXID": "SPDXRef-Package-MSVC-Runtime",
                "versionInfo": "NOASSERTION",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "Copyright Microsoft Corporation",
            },
            {
                "name": "Microsoft Universal C Runtime",
                "SPDXID": "SPDXRef-Package-Microsoft-UCRT",
                "versionInfo": "NOASSERTION",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "Copyright Microsoft Corporation",
            },
            {
                "name": "python-build-standalone",
                "SPDXID": "SPDXRef-Package-python-build-standalone",
                "versionInfo": PYTHON_BUILD_RELEASE,
                "downloadLocation": PYTHON_BUILD_SOURCE_URL,
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": PYTHON_BUILD_SOURCE_SHA256}
                ],
                "licenseConcluded": "MPL-2.0",
                "licenseDeclared": "MPL-2.0",
                "copyrightText": "NOASSERTION",
            },
        ]
    )
    binary_id = "SPDXRef-Package-MacroFlow-Binary"
    runtime_dependencies = {
        "SPDXRef-Package-PyQt6-Windows-Wheel",
        "SPDXRef-Package-PyQt6-Qt6-Windows-Wheel",
        "SPDXRef-Package-PyQt6-sip-Windows-Wheel",
        "SPDXRef-Package-python-build-standalone-Windows-Runtime",
        "SPDXRef-Package-MSVC-Runtime",
        "SPDXRef-Package-Microsoft-UCRT",
    }
    relationships = [
        {
            "spdxElementId": binary_id,
            "relationshipType": "GENERATED_FROM",
            "relatedSpdxElement": "SPDXRef-Package-MacroFlow",
        },
        *[
            {
                "spdxElementId": binary_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": package_id,
            }
            for package_id in sorted(runtime_dependencies)
        ],
        {
            "spdxElementId": binary_id,
            "relationshipType": "GENERATED_FROM",
            "relatedSpdxElement": "SPDXRef-Package-PyInstaller-Windows-Wheel",
        },
        {
            "spdxElementId": binary_id,
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": "SPDXRef-Package-PyInstaller-Bootloader",
        },
        {
            "spdxElementId": "SPDXRef-Package-PyQt6-Windows-Wheel",
            "relationshipType": "GENERATED_FROM",
            "relatedSpdxElement": "SPDXRef-Package-PyQt6",
        },
        {
            "spdxElementId": "SPDXRef-Package-PyQt6-sip-Windows-Wheel",
            "relationshipType": "GENERATED_FROM",
            "relatedSpdxElement": "SPDXRef-Package-PyQt6-sip",
        },
        {
            "spdxElementId": "SPDXRef-Package-PyInstaller-Windows-Wheel",
            "relationshipType": "CONTAINS",
            "relatedSpdxElement": "SPDXRef-Package-PyInstaller-Bootloader",
        },
        *[
            {
                "spdxElementId": "SPDXRef-Package-PyQt6-Qt6-Windows-Wheel",
                "relationshipType": "GENERATED_FROM",
                "relatedSpdxElement": package_id,
            }
            for package_id in (
                "SPDXRef-Package-Qt-Base",
                "SPDXRef-Package-Qt-SVG",
                "SPDXRef-Package-Qt-Image-Formats",
            )
        ],
        *[
            {
                "spdxElementId": "SPDXRef-Package-python-build-standalone-Windows-Runtime",
                "relationshipType": "GENERATED_FROM",
                "relatedSpdxElement": package_id,
            }
            for package_id in (
                "SPDXRef-Package-Python",
                "SPDXRef-Package-OpenSSL",
                "SPDXRef-Package-libffi",
                "SPDXRef-Package-bzip2",
                "SPDXRef-Package-XZ-liblzma",
                "SPDXRef-Package-python-build-standalone",
            )
        ],
    ]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{exe_name}-{tag}",
        "documentNamespace": f"https://github.com/{repository}/spdx/{commit}/{exe_hash}",
        "creationInfo": {"created": created, "creators": ["Tool: MacroFlow-build_release_bundle"]},
        "documentDescribes": [binary_id],
        "packages": spdx_packages,
        "relationships": relationships,
    }


def _zip_bytes(entries: dict[str, bytes]) -> bytes:
    with tempfile.SpooledTemporaryFile() as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(entries):
                info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, entries[name])
        stream.seek(0)
        return stream.read()


def build_bundle(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    commit = _validate_full_sha(args.commit)
    repository = _validate_repository(args.repository)
    tag = _validate_tag(args.tag)
    if re.fullmatch(r"[0-9]+", str(args.run_id)) is None:
        raise ValueError("run-id must contain decimal digits only")
    if re.fullmatch(r"[0-9]+", str(args.source_date_epoch)) is None:
        raise ValueError("source-date-epoch must contain decimal digits only")
    source_date_epoch = int(args.source_date_epoch)
    exe = args.exe.resolve()
    app_dir = args.app_dir.resolve()
    inventory = args.archive_inventory.resolve()
    if not exe.is_file() or exe.suffix.lower() != ".exe" or not exe.name.startswith("MacroFlow-v"):
        raise ValueError("exe must be an existing MacroFlow-v*.exe file")
    if not inventory.is_file():
        raise ValueError("archive inventory file does not exist")
    if not app_dir.is_dir() or exe.parent != app_dir:
        raise ValueError("app-dir must be the onedir directory containing the executable")
    app_files = sorted(path for path in app_dir.rglob("*") if path.is_file())
    if not app_files or any(path.is_symlink() for path in app_dir.rglob("*")):
        raise ValueError("app-dir must contain regular files and no symbolic links")
    inventory_bytes = inventory.read_bytes()
    if b"PyQt6" not in inventory_bytes or b"Qt6Core" not in inventory_bytes:
        raise ValueError("archive inventory does not contain the required PyQt6/Qt6 runtime")
    actual_paths = "\n".join(path.relative_to(app_dir).as_posix() for path in app_files).encode(
        "utf-8"
    )
    normalized_inventory = (inventory_bytes + b"\n" + actual_paths).replace(b"\\", b"/").lower()
    if re.search(rb"(?:qt6?pdf|qpdf)", normalized_inventory):
        raise ValueError("archive inventory contains an unreviewed Qt PDF payload")
    if b"opengl32sw.dll" in normalized_inventory:
        raise ValueError("archive inventory contains an unreviewed native payload: opengl32sw.dll")
    reviewed_qt_modules = {
        b"qt6core.dll",
        b"qt6gui.dll",
        b"qt6network.dll",
        b"qt6svg.dll",
        b"qt6widgets.dll",
    }
    bundled_qt_modules = set(re.findall(rb"qt6[a-z0-9_]+\.dll", normalized_inventory))
    unexpected_qt_modules = bundled_qt_modules - reviewed_qt_modules
    if unexpected_qt_modules:
        names = ", ".join(name.decode("ascii") for name in sorted(unexpected_qt_modules))
        raise ValueError(f"archive inventory contains an unreviewed Qt runtime module: {names}")
    reviewed_qt_plugins = {
        b"generic/qtuiotouchplugin.dll",
        b"iconengines/qsvgicon.dll",
        b"imageformats/qgif.dll",
        b"imageformats/qicns.dll",
        b"imageformats/qico.dll",
        b"imageformats/qjpeg.dll",
        b"imageformats/qsvg.dll",
        b"imageformats/qtga.dll",
        b"imageformats/qtiff.dll",
        b"imageformats/qwbmp.dll",
        b"imageformats/qwebp.dll",
        b"platforms/qminimal.dll",
        b"platforms/qoffscreen.dll",
        b"platforms/qwindows.dll",
        b"styles/qmodernwindowsstyle.dll",
    }
    bundled_qt_plugins = {
        match.removeprefix(b"pyqt6/qt6/plugins/")
        for match in re.findall(
            rb"pyqt6/qt6/plugins/[a-z0-9_./-]+\.dll",
            normalized_inventory,
        )
    }
    unexpected_qt_plugins = bundled_qt_plugins - reviewed_qt_plugins
    if unexpected_qt_plugins:
        names = ", ".join(name.decode("ascii") for name in sorted(unexpected_qt_plugins))
        raise ValueError(f"archive inventory contains an unreviewed Qt plugin: {names}")

    reviewed_internal_native_paths = {
        b"_bz2.pyd",
        b"_ctypes.pyd",
        b"_decimal.pyd",
        b"_hashlib.pyd",
        b"_lzma.pyd",
        b"_socket.pyd",
        b"_uuid.pyd",
        b"libcrypto-3-x64.dll",
        b"libffi-8.dll",
        b"pyqt6/qtcore.pyd",
        b"pyqt6/qtgui.pyd",
        b"pyqt6/qtwidgets.pyd",
        b"pyqt6/sip.cp311-win_amd64.pyd",
        b"python3.dll",
        b"python311.dll",
        b"select.pyd",
        b"ucrtbase.dll",
        b"unicodedata.pyd",
        b"vcruntime140.dll",
        b"vcruntime140_1.dll",
        b"api-ms-win-core-console-l1-1-0.dll",
        b"api-ms-win-core-datetime-l1-1-0.dll",
        b"api-ms-win-core-debug-l1-1-0.dll",
        b"api-ms-win-core-errorhandling-l1-1-0.dll",
        b"api-ms-win-core-file-l1-1-0.dll",
        b"api-ms-win-core-file-l1-2-0.dll",
        b"api-ms-win-core-file-l2-1-0.dll",
        b"api-ms-win-core-fibers-l1-1-0.dll",
        b"api-ms-win-core-fibers-l1-1-1.dll",
        b"api-ms-win-core-handle-l1-1-0.dll",
        b"api-ms-win-core-heap-l1-1-0.dll",
        b"api-ms-win-core-interlocked-l1-1-0.dll",
        b"api-ms-win-core-kernel32-legacy-l1-1-1.dll",
        b"api-ms-win-core-libraryloader-l1-1-0.dll",
        b"api-ms-win-core-localization-l1-2-0.dll",
        b"api-ms-win-core-memory-l1-1-0.dll",
        b"api-ms-win-core-namedpipe-l1-1-0.dll",
        b"api-ms-win-core-processenvironment-l1-1-0.dll",
        b"api-ms-win-core-processthreads-l1-1-0.dll",
        b"api-ms-win-core-processthreads-l1-1-1.dll",
        b"api-ms-win-core-profile-l1-1-0.dll",
        b"api-ms-win-core-rtlsupport-l1-1-0.dll",
        b"api-ms-win-core-string-l1-1-0.dll",
        b"api-ms-win-core-synch-l1-1-0.dll",
        b"api-ms-win-core-synch-l1-2-0.dll",
        b"api-ms-win-core-sysinfo-l1-1-0.dll",
        b"api-ms-win-core-sysinfo-l1-2-0.dll",
        b"api-ms-win-core-timezone-l1-1-0.dll",
        b"api-ms-win-core-util-l1-1-0.dll",
        b"api-ms-win-crt-conio-l1-1-0.dll",
        b"api-ms-win-crt-convert-l1-1-0.dll",
        b"api-ms-win-crt-environment-l1-1-0.dll",
        b"api-ms-win-crt-filesystem-l1-1-0.dll",
        b"api-ms-win-crt-heap-l1-1-0.dll",
        b"api-ms-win-crt-locale-l1-1-0.dll",
        b"api-ms-win-crt-math-l1-1-0.dll",
        b"api-ms-win-crt-multibyte-l1-1-0.dll",
        b"api-ms-win-crt-private-l1-1-0.dll",
        b"api-ms-win-crt-process-l1-1-0.dll",
        b"api-ms-win-crt-runtime-l1-1-0.dll",
        b"api-ms-win-crt-stdio-l1-1-0.dll",
        b"api-ms-win-crt-string-l1-1-0.dll",
        b"api-ms-win-crt-time-l1-1-0.dll",
        b"api-ms-win-crt-utility-l1-1-0.dll",
    }
    reviewed_qt_runtime_support = {
        b"msvcp140.dll",
        b"msvcp140_1.dll",
        b"msvcp140_2.dll",
        b"vcruntime140.dll",
        b"vcruntime140_1.dll",
    }
    reviewed_native_paths = {
        b"_internal/" + path for path in reviewed_internal_native_paths
    }
    native_paths: set[bytes] = set()
    for path in app_files:
        if path.suffix.lower() not in {".dll", ".pyd", ".exe"}:
            continue
        relative = path.relative_to(app_dir).as_posix()
        try:
            canonical = relative.encode("ascii").lower()
        except UnicodeEncodeError as exc:
            raise ValueError(
                "archive inventory contains an unreviewed native payload with a "
                f"non-ASCII path: {relative}"
            ) from exc
        native_paths.add(canonical)

    def is_reviewed_native(path: bytes) -> bool:
        if path in reviewed_native_paths or path == exe.name.lower().encode("ascii"):
            return True
        if path.startswith(b"_internal/pyqt6/qt6/bin/"):
            relative = path.removeprefix(b"_internal/pyqt6/qt6/bin/")
            if b"/" in relative:
                return False
            return relative in bundled_qt_modules or relative in reviewed_qt_runtime_support
        if path.startswith(b"_internal/pyqt6/qt6/plugins/"):
            relative = path.removeprefix(b"_internal/pyqt6/qt6/plugins/")
            return relative in reviewed_qt_plugins
        return False

    unexpected_native_paths = {path for path in native_paths if not is_reviewed_native(path)}
    if unexpected_native_paths:
        names = ", ".join(name.decode("utf-8", errors="replace") for name in sorted(unexpected_native_paths))
        raise ValueError(f"archive inventory contains an unreviewed native payload: {names}")
    if platform.python_version() != PYTHON_VERSION:
        raise ValueError(f"release bundle must be built with Python {PYTHON_VERSION}")
    _verify_python_build_release()

    required_paths = [ROOT / name for name in STATIC_FILES]
    required_paths.extend(ROOT / "licenses" / name for name in LICENSE_FILES)
    missing = [str(path.relative_to(ROOT)) for path in required_paths if not path.is_file()]
    if missing:
        raise ValueError(f"missing compliance files: {missing}")

    packages = _locked_packages()
    _validate_release_identity(
        exe_name=exe.name,
        tag=tag,
        run_number=str(args.run_number),
        project_version=str(packages["macroflow"]["version"]),
    )
    exe_bytes = exe.read_bytes()
    exe_hash = _sha256(exe_bytes)
    source_text = _source_code_markdown(
        repository=repository, commit=commit, tag=tag, packages=packages
    ).encode("utf-8")
    sbom = _spdx_document(
        repository=repository,
        commit=commit,
        tag=tag,
        exe_name=exe.name,
        exe_hash=exe_hash,
        packages=packages,
        source_date_epoch=source_date_epoch,
    )
    sbom_bytes = (json.dumps(sbom, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )

    prefix = f"{exe.stem}/"
    entries = {
        prefix + path.relative_to(app_dir).as_posix(): path.read_bytes() for path in app_files
    }
    entries.update({prefix + path.name: path.read_bytes() for path in required_paths[: len(STATIC_FILES)]})
    entries.update(
        {
            prefix + "licenses/" + path.name: path.read_bytes()
            for path in required_paths[len(STATIC_FILES) :]
        }
    )
    entries[prefix + "SOURCE_CODE.md"] = source_text
    entries[prefix + "SBOM.spdx.json"] = sbom_bytes
    entries[prefix + "PYINSTALLER_CONTENTS.txt"] = inventory_bytes

    zip_bytes = _zip_bytes(entries)
    output_dir = args.output_dir.resolve()
    output_parent = output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        raise ValueError("output-dir must not already exist")

    bundle_name = f"{exe.stem}-GPL.zip"
    checksum_name = f"{bundle_name}.sha256"
    provenance_name = f"{bundle_name}.provenance.txt"
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_parent))
    try:
        staged_bundle = staging / bundle_name
        staged_checksum = staging / checksum_name
        staged_provenance = staging / provenance_name
        staged_bundle.write_bytes(zip_bytes)
        staged_checksum.write_text(f"{_sha256(zip_bytes)}  {bundle_name}\n", encoding="ascii")
        staged_provenance.write_text(
            "\n".join(
                [
                    f"commit={commit}",
                    f"tag={tag}",
                    f"run_id={args.run_id}",
                    f"run_number={args.run_number}",
                    f"repository={repository}",
                    f"source_date_epoch={source_date_epoch}",
                    f"python={platform.python_version()}",
                    f"python_build_release={PYTHON_BUILD_RELEASE}",
                    f"python_build_source_commit={PYTHON_BUILD_SOURCE_COMMIT}",
                    f"python_build_source_sha256={PYTHON_BUILD_SOURCE_SHA256}",
                    f"pyqt6_source_sha256={PYQT6_SOURCE_SHA256}",
                    f"qtbase_source_sha256={QTBASE_SOURCE_SHA256}",
                    f"qtsvg_source_sha256={QTSVG_SOURCE_SHA256}",
                    f"qtimageformats_source_sha256={QTIMAGEFORMATS_SOURCE_SHA256}",
                    f"openssl_source_sha256={OPENSSL_SOURCE_SHA256}",
                    f"libffi_source_sha256={LIBFFI_SOURCE_SHA256}",
                    f"bzip2_source_sha256={BZIP2_SOURCE_SHA256}",
                    f"xz_source_sha256={XZ_SOURCE_SHA256}",
                    f"python_source_sha256={PYTHON_SOURCE_SHA256}",
                    f"pyqt6_sip_source_sha256={PYQT6_SIP_SOURCE_SHA256}",
                    f"pyinstaller_source_sha256={PYINSTALLER_SOURCE_SHA256}",
                    f"pyqt6_windows_wheel_url={PYQT6_WINDOWS_WHEEL_URL}",
                    f"pyqt6_windows_wheel_sha256={PYQT6_WINDOWS_WHEEL_SHA256}",
                    f"pyqt6_qt6_windows_wheel_url={PYQT6_QT6_WINDOWS_WHEEL_URL}",
                    f"pyqt6_qt6_windows_wheel_sha256={PYQT6_QT6_WINDOWS_WHEEL_SHA256}",
                    f"pyqt6_sip_windows_wheel_url={PYQT6_SIP_WINDOWS_WHEEL_URL}",
                    f"pyqt6_sip_windows_wheel_sha256={PYQT6_SIP_WINDOWS_WHEEL_SHA256}",
                    f"pyinstaller_windows_wheel_url={PYINSTALLER_WINDOWS_WHEEL_URL}",
                    f"pyinstaller_windows_wheel_sha256={PYINSTALLER_WINDOWS_WHEEL_SHA256}",
                    f"python_windows_runtime_url={PYTHON_WINDOWS_RUNTIME_URL}",
                    f"python_windows_runtime_sha256={PYTHON_WINDOWS_RUNTIME_SHA256}",
                    f"exe_sha256={exe_hash}",
                    f"bundle_sha256={_sha256(zip_bytes)}",
                    "license=GPL-3.0-only",
                    "",
                ]
            ),
            encoding="ascii",
        )
        for staged_file in (staged_bundle, staged_checksum, staged_provenance):
            with staged_file.open("r+b") as stream:
                os.fsync(stream.fileno())
        os.replace(staging, output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    bundle = output_dir / bundle_name
    checksum = output_dir / checksum_name
    provenance = output_dir / provenance_name
    return bundle, checksum, provenance


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--archive-inventory", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-number", required=True)
    parser.add_argument("--source-date-epoch", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    try:
        bundle, checksum, provenance = build_bundle(_parse_args())
    except (OSError, ValueError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise SystemExit(f"release bundle error: {exc}") from exc
    print(f"bundle={bundle}")
    print(f"checksum={checksum}")
    print(f"provenance={provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
