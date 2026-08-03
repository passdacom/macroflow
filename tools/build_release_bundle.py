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
LICENSE_FILES = (
    "GPL-3.0-only.txt",
    "LGPL-3.0-only.txt",
    "BSD-2-Clause-PyQt6-sip.txt",
    "PSF-2.0-Python.txt",
    "MPL-2.0-python-build-standalone.txt",
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
    "macroflow": "1.6.1",
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
        "",
        "The complete build procedure is in `BUILDING.md`. The following exact upstream source",
        "locations correspond to components included by the locked Windows build:",
        "",
    ]
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
        if name == "macroflow":
            item["downloadLocation"] = f"https://github.com/{repository}/tree/{commit}"
        spdx_packages.append(item)

    spdx_packages.extend(
        [
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
                "downloadLocation": packages["pyinstaller"]["sdist"]["url"],
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "GPL-2.0-or-later",
                "licenseComments": "PyInstaller bootloader exception text is included in licenses/PyInstaller-COPYING.txt.",
                "copyrightText": "NOASSERTION",
            },
            {
                "name": "Python",
                "SPDXID": "SPDXRef-Package-Python",
                "versionInfo": PYTHON_VERSION,
                "downloadLocation": PYTHON_SOURCE_URL,
                "filesAnalyzed": False,
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
    relationships = [
        {
            "spdxElementId": binary_id,
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": package["SPDXID"],
        }
        for package in spdx_packages
        if package["SPDXID"] != binary_id
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
    normalized_inventory = inventory_bytes.replace(b"\\", b"/").lower()
    if re.search(rb"(?:qt6?pdf|qpdf)", normalized_inventory):
        raise ValueError("archive inventory contains an unreviewed Qt PDF payload")
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
