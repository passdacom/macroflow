"""GPL release-compliance contracts for public MacroFlow distributions."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import yaml
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document

ROOT = Path(__file__).resolve().parents[1]
PROJECT_VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
    "project"
]["version"]
WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"
LICENSE_FILES = {
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
}
REQUIRED_BUNDLE_FILES = {
    "LICENSE",
    "COPYRIGHT",
    "README.md",
    "BUILDING.md",
    "THIRD_PARTY_NOTICES.md",
    "SOURCE_CODE.md",
    "SBOM.spdx.json",
    "PYINSTALLER_CONTENTS.txt",
    *(f"licenses/{name}" for name in LICENSE_FILES),
}
COMPANION_SOURCE_ASSETS = {
    "pyqt6-6.11.0.tar.gz": "45dd60aa69976de1918b5ced6b4e7b6a25abd2a919ecef5fd5826ecc76718889",
    "qtbase-everywhere-src-6.11.0.tar.xz": "231ad85979864d914dc9568a1b71c91d6cf20d7b2021d059103bf0eb51cb755e",
    "qtsvg-everywhere-src-6.11.0.tar.xz": "dfa8d653be07087d9407ed4a4ebae847f8953e0b7abd829f089803ab652a30e6",
    "qtimageformats-everywhere-src-6.11.0.tar.xz": (
        "d3adb02ac5e2fe24068dbdaee0d7cc68cc3fa8553291c1bfce77c9fe8e940cc8"
    ),
    "openssl-3.5.6.tar.gz": (
        "deae7c80cba99c4b4f940ecadb3c3338b13cb77418409238e57d7f31f2a3b736"
    ),
    "libffi-3.4.6.tar.gz": (
        "b0dea9df23c863a7a50e825440f3ebffabd65df1497108e5d437747843895a4e"
    ),
    "bzip2-1.0.8.tar.gz": (
        "ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269"
    ),
    "xz-5.8.1.tar.gz": (
        "507825b599356c10dca1cd720c9d0d0c9d5400b9de300af00e4d1ea150795543"
    ),
    "Python-3.11.15.tar.xz": (
        "272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625"
    ),
    "pyqt6_sip-13.11.1.tar.gz": (
        "869c5b48afe38e55b1ee0dd72182b0886e968cc509b98023ff50010b013ce1be"
    ),
    "pyinstaller-6.19.0.tar.gz": (
        "ec73aeb8bd9b7f2f1240d328a4542e90b3c6e6fbc106014778431c616592a865"
    ),
    "python-build-standalone-20260414-7af98d60e411de479ab16f5537efc7184dffc25a.tar.gz": (
        "8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c"
    ),
}


def _workflow() -> dict[str, object]:
    parsed = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    if True in parsed and "on" not in parsed:
        parsed["on"] = parsed.pop(True)
    return parsed


def _steps(job: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(step.get("name", step.get("uses", ""))): step
        for step in job["steps"]  # type: ignore[index,union-attr]
    }


def test_project_declares_gplv3_and_public_distribution_metadata() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["license"] == "GPL-3.0-only"
    assert project["readme"] == "README.md"
    assert project["urls"]["Source"] == "https://github.com/passdacom/macroflow"
    assert "내부 배포용" not in project["description"]

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 29 June 2007" in license_text
    assert "GNU General Public License v3.0" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )
    copyright_text = (ROOT / "COPYRIGHT").read_text(encoding="utf-8")
    assert "Han Phillip" in copyright_text
    assert "Git history" not in copyright_text
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "EXE만 분리해 재배포하지 마십시오" not in readme
    assert "GPLv3 제6조" in readme
    about_source = (ROOT / "src/macroflow/ui/main_window.py").read_text(encoding="utf-8")
    assert "Qt 6.11.0: GNU LGPLv3" in about_source
    assert "SOURCE_CODE.md" in about_source


def test_runtime_license_bundle_and_notices_are_checked_in() -> None:
    license_dir = ROOT / "licenses"
    assert {path.name for path in license_dir.iterdir() if path.is_file()} == LICENSE_FILES
    exact_source_license_hashes = {
        "libffi-MIT.txt": "67894089811f93fca47a76f85e017da6f8582d4ba0905963c6e0f1ad6df7a195",
        "bzip2-1.0.8.txt": "c6dbbf828498be844a89eaa3b84adbab3199e342eb5cb2ed2f0d4ba7ec0f38a3",
    }
    for name, expected in exact_source_license_hashes.items():
        assert hashlib.sha256((license_dir / name).read_bytes()).hexdigest() == expected

    assert "1996-2024" in (license_dir / "libffi-MIT.txt").read_text(encoding="utf-8")
    bzip2_license = (license_dir / "bzip2-1.0.8.txt").read_text(encoding="utf-8")
    assert "1996-2019" in bzip2_license
    assert "version 1.0.8 of 13 July 2019" in bzip2_license

    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for required in (
        "PyQt6 6.11.0",
        "GPL-3.0-only",
        "PyQt6-Qt6 6.11.0",
        "LGPL-3.0-only",
        "PyQt6-sip 13.11.1",
        "BSD-2-Clause",
        "Python 3.11.15",
        "PSF-2.0",
        "python-build-standalone 20260414",
        "MPL-2.0",
        "PyInstaller 6.19.0",
        "OpenSSL 3.5.6",
        "Apache-2.0",
        "libffi 3.4.6",
        "MIT",
        "bzip2 1.0.8",
        "XZ Utils 5.8.1",
        "0BSD",
        "Microsoft Visual C++ Runtime",
        "Microsoft Universal C Runtime",
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
    ):
        assert required in notices


def test_bundle_builder_packages_exe_source_pointer_notices_and_spdx(tmp_path: Path) -> None:
    app_dir = tmp_path / "MacroFlow"
    runtime_dir = app_dir / "_internal" / "PyQt6" / "Qt6" / "bin"
    runtime_dir.mkdir(parents=True)
    exe = app_dir / f"MacroFlow-v{PROJECT_VERSION}-build999.exe"
    exe.write_bytes(b"MZ\x00macroflow-test")
    (runtime_dir / "Qt6Core.dll").write_bytes(b"qt-runtime")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text("PyQt6\\QtCore.pyd\nPyQt6\\Qt6\\bin\\Qt6Core.dll\n", encoding="utf-8")
    output = tmp_path / "release"
    commit = "a" * 40
    tag = f"v{PROJECT_VERSION}-build999"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_release_bundle.py"),
            "--exe",
            str(exe),
            "--app-dir",
            str(app_dir),
            "--archive-inventory",
            str(inventory),
            "--repository",
            "passdacom/macroflow",
            "--commit",
            commit,
            "--tag",
            tag,
            "--run-id",
            "12345",
            "--run-number",
            "999",
            "--source-date-epoch",
            "1785710000",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    bundle = output / f"MacroFlow-v{PROJECT_VERSION}-build999-GPL.zip"
    checksum = output / f"{bundle.name}.sha256"
    provenance = output / f"{bundle.name}.provenance.txt"
    assert bundle.is_file()
    assert checksum.is_file()
    assert provenance.is_file()

    second_output = tmp_path / "release-second"
    second_command = [*result.args[:-1], str(second_output)]
    second = subprocess.run(
        second_command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert second.returncode == 0, second.stderr
    assert bundle.read_bytes() == (second_output / bundle.name).read_bytes()

    recorded_hash, recorded_name = checksum.read_text(encoding="ascii").strip().split("  ")
    assert recorded_name == bundle.name
    assert recorded_hash == hashlib.sha256(bundle.read_bytes()).hexdigest()

    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
        prefix = f"MacroFlow-v{PROJECT_VERSION}-build999/"
        assert prefix + exe.name in names
        assert prefix + "_internal/PyQt6/Qt6/bin/Qt6Core.dll" in names
        assert {prefix + name for name in REQUIRED_BUNDLE_FILES} <= names
        source = archive.read(prefix + "SOURCE_CODE.md").decode("utf-8")
        assert commit in source
        assert tag in source
        assert f"https://github.com/passdacom/macroflow/tree/{commit}" in source
        assert "https://www.python.org/ftp/python/3.11.15/Python-3.11.15.tar.xz" in source
        assert "272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625" in source
        assert "7af98d60e411de479ab16f5537efc7184dffc25a" in source
        assert "8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c" in source
        assert "codeload.github.com/astral-sh/python-build-standalone/tar.gz/7af98d60e411de479ab16f5537efc7184dffc25a" in source
        assert "attached to the same GitHub Release" in source
        assert "Equivalent network access" in source
        assert "written offer" not in source.lower()
        assert f"MacroFlow-{tag}-source.tar.gz" in source
        assert f"MacroFlow-{tag}-source.tar.gz.sha256" in source
        for name, digest in COMPANION_SOURCE_ASSETS.items():
            assert name in source
            assert f"{name}.sha256" in source
            assert digest in source
        sbom = json.loads(archive.read(prefix + "SBOM.spdx.json"))

    sbom_path = tmp_path / "SBOM.spdx.json"
    sbom_path.write_text(json.dumps(sbom), encoding="utf-8")
    validation_messages = validate_full_spdx_document(parse_file(str(sbom_path)))
    assert validation_messages == []

    package_licenses = {
        package["name"]: package["licenseConcluded"] for package in sbom["packages"]
    }
    assert package_licenses["MacroFlow"] == "GPL-3.0-only"
    assert package_licenses["PyQt6"] == "GPL-3.0-only"
    assert package_licenses["PyQt6-Qt6"] == "NOASSERTION"
    assert package_licenses["PyQt6 Windows wheel"] == "GPL-3.0-only"
    assert package_licenses["PyQt6-Qt6 Windows wheel"] == "NOASSERTION"
    assert package_licenses["PyQt6-sip Windows wheel"] == "BSD-2-Clause"
    assert package_licenses["PyInstaller Windows wheel"] == (
        "GPL-2.0-or-later WITH Bootloader-exception"
    )
    assert package_licenses["python-build-standalone Windows runtime"] == "NOASSERTION"
    assert package_licenses["Qt Base"] == "NOASSERTION"
    assert package_licenses["Qt SVG"] == "NOASSERTION"
    assert package_licenses["Qt Image Formats"] == "NOASSERTION"
    assert package_licenses["PyQt6-sip"] == "BSD-2-Clause"
    assert package_licenses["Python"] == "PSF-2.0"
    assert package_licenses["python-build-standalone"] == "MPL-2.0"
    assert package_licenses["OpenSSL"] == "Apache-2.0"
    assert package_licenses["libffi"] == "MIT"
    assert package_licenses["bzip2"] == "bzip2-1.0.6"
    bzip2_package = next(package for package in sbom["packages"] if package["name"] == "bzip2")
    assert bzip2_package["copyrightText"] == (
        "Copyright (C) 1996-2019 Julian R Seward"
    )
    assert package_licenses["XZ Utils liblzma"] == "0BSD"
    assert package_licenses["Microsoft Visual C++ Runtime"] == "NOASSERTION"
    assert package_licenses["Microsoft Universal C Runtime"] == "NOASSERTION"
    assert package_licenses["MacroFlow Windows Distribution"] == "GPL-3.0-only"
    assert package_licenses["PyInstaller Bootloader"] == (
        "GPL-2.0-or-later WITH Bootloader-exception"
    )
    relationships = {
        (
            relationship["spdxElementId"],
            relationship["relationshipType"],
            relationship["relatedSpdxElement"],
        )
        for relationship in sbom["relationships"]
    }
    assert (
        "SPDXRef-Package-MacroFlow-Binary",
        "GENERATED_FROM",
        "SPDXRef-Package-MacroFlow",
    ) in relationships
    assert (
        "SPDXRef-Package-MacroFlow-Binary",
        "GENERATED_FROM",
        "SPDXRef-Package-PyInstaller-Windows-Wheel",
    ) in relationships
    assert (
        "SPDXRef-Package-python-build-standalone-Windows-Runtime",
        "GENERATED_FROM",
        "SPDXRef-Package-python-build-standalone",
    ) in relationships
    assert (
        "SPDXRef-Package-MacroFlow-Binary",
        "DEPENDS_ON",
        "SPDXRef-Package-python-build-standalone",
    ) not in relationships
    bootloader = next(
        package for package in sbom["packages"] if package["name"] == "PyInstaller Bootloader"
    )
    assert bootloader["licenseDeclared"] == "GPL-2.0-or-later WITH Bootloader-exception"
    pyqt6_wheel = next(
        package for package in sbom["packages"] if package["name"] == "PyQt6 Windows wheel"
    )
    assert pyqt6_wheel["downloadLocation"].endswith(
        "/pyqt6-6.11.0-cp310-abi3-win_amd64.whl"
    )
    assert pyqt6_wheel["checksums"] == [
        {
            "algorithm": "SHA256",
            "checksumValue": "bd11b459c54dca068e988a42cf838303334f0d441b9d16d92ae6719fcb5ac6ba",
        }
    ]
    qt_wheel = next(
        package
        for package in sbom["packages"]
        if package["name"] == "PyQt6-Qt6 Windows wheel"
    )
    assert qt_wheel["downloadLocation"].endswith(
        "/pyqt6_qt6-6.11.0-py3-none-win_amd64.whl"
    )
    assert qt_wheel["checksums"] == [
        {
            "algorithm": "SHA256",
            "checksumValue": "b0e42629cef2575f2178aaeb32b0e539291df869f91f4df48983da3ccaad05af",
        }
    ]
    binary_origins = {
        "PyQt6-sip Windows wheel": (
            "pyqt6_sip-13.11.1-cp311-cp311-win_amd64.whl",
            "98db8ed37cf08130e1ee74b8ff47a6bfb8c3cdfe826310597a630a50e47feedc",
        ),
        "PyInstaller Windows wheel": (
            "pyinstaller-6.19.0-py3-none-win_amd64.whl",
            "b5bb6536c6560330d364d91522250f254b107cf69129d9cbcd0e6727c570be33",
        ),
        "python-build-standalone Windows runtime": (
            "cpython-3.11.15%2B20260414-x86_64-pc-windows-msvc-install_only_stripped.tar.gz",
            "71ffdf290e0483f0881e02518ecb9cedb449807856ae7dc76aa630e5acd00919",
        ),
    }
    for package_name, (url_suffix, digest) in binary_origins.items():
        package = next(item for item in sbom["packages"] if item["name"] == package_name)
        assert package["downloadLocation"].endswith(url_suffix)
        assert package["checksums"] == [
            {"algorithm": "SHA256", "checksumValue": digest}
        ]
    python_build_package = next(
        package for package in sbom["packages"] if package["name"] == "python-build-standalone"
    )
    assert python_build_package["downloadLocation"].endswith(
        "/7af98d60e411de479ab16f5537efc7184dffc25a"
    )
    assert python_build_package["checksums"] == [
        {
            "algorithm": "SHA256",
            "checksumValue": "8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c",
        }
    ]
    for package_name, digest in (
        ("PyQt6", COMPANION_SOURCE_ASSETS["pyqt6-6.11.0.tar.gz"]),
        ("Qt Base", COMPANION_SOURCE_ASSETS["qtbase-everywhere-src-6.11.0.tar.xz"]),
        ("Qt SVG", COMPANION_SOURCE_ASSETS["qtsvg-everywhere-src-6.11.0.tar.xz"]),
        (
            "Qt Image Formats",
            COMPANION_SOURCE_ASSETS["qtimageformats-everywhere-src-6.11.0.tar.xz"],
        ),
        ("OpenSSL", COMPANION_SOURCE_ASSETS["openssl-3.5.6.tar.gz"]),
        ("libffi", COMPANION_SOURCE_ASSETS["libffi-3.4.6.tar.gz"]),
        ("bzip2", COMPANION_SOURCE_ASSETS["bzip2-1.0.8.tar.gz"]),
        ("XZ Utils liblzma", COMPANION_SOURCE_ASSETS["xz-5.8.1.tar.gz"]),
        ("Python", COMPANION_SOURCE_ASSETS["Python-3.11.15.tar.xz"]),
        ("PyQt6-sip", COMPANION_SOURCE_ASSETS["pyqt6_sip-13.11.1.tar.gz"]),
        ("PyInstaller Bootloader", COMPANION_SOURCE_ASSETS["pyinstaller-6.19.0.tar.gz"]),
    ):
        package = next(item for item in sbom["packages"] if item["name"] == package_name)
        assert package["checksums"] == [
            {"algorithm": "SHA256", "checksumValue": digest}
        ]
    provenance_text = provenance.read_text(encoding="ascii")
    assert "python_build_source_commit=7af98d60e411de479ab16f5537efc7184dffc25a" in provenance_text
    assert (
        "python_build_source_sha256=8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c"
        in provenance_text
    )
    assert f"pyqt6_source_sha256={COMPANION_SOURCE_ASSETS['pyqt6-6.11.0.tar.gz']}" in provenance_text
    assert (
        f"qtbase_source_sha256={COMPANION_SOURCE_ASSETS['qtbase-everywhere-src-6.11.0.tar.xz']}"
        in provenance_text
    )
    assert (
        f"qtsvg_source_sha256={COMPANION_SOURCE_ASSETS['qtsvg-everywhere-src-6.11.0.tar.xz']}"
        in provenance_text
    )
    assert (
        "qtimageformats_source_sha256="
        f"{COMPANION_SOURCE_ASSETS['qtimageformats-everywhere-src-6.11.0.tar.xz']}"
        in provenance_text
    )
    assert (
        f"openssl_source_sha256={COMPANION_SOURCE_ASSETS['openssl-3.5.6.tar.gz']}"
        in provenance_text
    )
    assert (
        f"libffi_source_sha256={COMPANION_SOURCE_ASSETS['libffi-3.4.6.tar.gz']}"
        in provenance_text
    )
    assert (
        f"bzip2_source_sha256={COMPANION_SOURCE_ASSETS['bzip2-1.0.8.tar.gz']}"
        in provenance_text
    )
    assert (
        f"xz_source_sha256={COMPANION_SOURCE_ASSETS['xz-5.8.1.tar.gz']}"
        in provenance_text
    )
    assert (
        f"python_source_sha256={COMPANION_SOURCE_ASSETS['Python-3.11.15.tar.xz']}"
        in provenance_text
    )
    assert (
        f"pyqt6_sip_source_sha256={COMPANION_SOURCE_ASSETS['pyqt6_sip-13.11.1.tar.gz']}"
        in provenance_text
    )
    assert (
        f"pyinstaller_source_sha256={COMPANION_SOURCE_ASSETS['pyinstaller-6.19.0.tar.gz']}"
        in provenance_text
    )
    assert (
        "pyqt6_windows_wheel_url="
        "https://files.pythonhosted.org/packages/6f/85/dd9f03d78d87460e109e0121cd6201c5802bdd655656bf2780e964870fea/pyqt6-6.11.0-cp310-abi3-win_amd64.whl"
        in provenance_text
    )
    assert (
        "pyqt6_windows_wheel_sha256="
        "bd11b459c54dca068e988a42cf838303334f0d441b9d16d92ae6719fcb5ac6ba"
        in provenance_text
    )
    assert (
        "pyqt6_qt6_windows_wheel_url="
        "https://files.pythonhosted.org/packages/36/cd/da0147d331b44587a7214c7f59719ac4f8e9433b268016962b02067007d1/pyqt6_qt6-6.11.0-py3-none-win_amd64.whl"
        in provenance_text
    )
    assert (
        "pyqt6_qt6_windows_wheel_sha256="
        "b0e42629cef2575f2178aaeb32b0e539291df869f91f4df48983da3ccaad05af"
        in provenance_text
    )
    for key, digest in (
        (
            "pyqt6_sip_windows_wheel_sha256",
            "98db8ed37cf08130e1ee74b8ff47a6bfb8c3cdfe826310597a630a50e47feedc",
        ),
        (
            "pyinstaller_windows_wheel_sha256",
            "b5bb6536c6560330d364d91522250f254b107cf69129d9cbcd0e6727c570be33",
        ),
        (
            "python_windows_runtime_sha256",
            "71ffdf290e0483f0881e02518ecb9cedb449807856ae7dc76aa630e5acd00919",
        ),
    ):
        assert f"{key}={digest}" in provenance_text


def test_workflow_mirrors_all_reviewed_runtime_sources_with_checksums() -> None:
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    workflow = _workflow()
    build_steps = _steps(workflow["jobs"]["build-exe"])  # type: ignore[index]
    release_step = build_steps["Build GPL distribution bundle"]
    release_body = _steps(workflow["jobs"]["release"])["Create release"]["with"]["body"]  # type: ignore[index]

    run = str(release_step["run"])
    for name, digest in COMPANION_SOURCE_ASSETS.items():
        assert name in run
        assert digest in workflow_text

    assert '"release/$($source.Name).sha256"' in run
    assert "git -c core.autocrlf=false archive --format=tar.gz" in run
    assert "MacroFlow-$env:TAG-source.tar.gz" in run

    assert "download.qt.io/archive/qt/6.11/6.11.0/submodules/qtbase" in run
    assert "download.qt.io/archive/qt/6.11/6.11.0/submodules/qtsvg" in run
    assert "files.pythonhosted.org" in run
    assert "openssl/releases/download/openssl-3.5.6" in run
    assert "libffi/releases/download/v3.4.6" in run
    assert "Get-FileHash -Algorithm SHA256" in run
    assert "exact reviewed runtime companion source archives" in str(release_body)


def test_bundle_builder_rejects_non_full_commit(tmp_path: Path) -> None:
    app_dir = tmp_path / "MacroFlow"
    app_dir.mkdir()
    exe = app_dir / f"MacroFlow-v{PROJECT_VERSION}-build999.exe"
    exe.write_bytes(b"MZ")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text("inventory", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_release_bundle.py"),
            "--exe",
            str(exe),
            "--app-dir",
            str(app_dir),
            "--archive-inventory",
            str(inventory),
            "--repository",
            "passdacom/macroflow",
            "--commit",
            "abc123",
            "--tag",
            f"v{PROJECT_VERSION}-build999",
            "--run-id",
            "12345",
            "--run-number",
            "999",
            "--source-date-epoch",
            "1785710000",
            "--output-dir",
            str(tmp_path / "release"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "40-character lowercase Git SHA" in result.stderr


def test_bundle_builder_opens_staged_outputs_writable_for_windows_fsync() -> None:
    source = (ROOT / "tools" / "build_release_bundle.py").read_text(encoding="utf-8")

    assert 'with staged_file.open("r+b") as stream:' in source


def test_bundle_builder_rejects_version_or_build_mismatch(tmp_path: Path) -> None:
    app_dir = tmp_path / "MacroFlow"
    app_dir.mkdir()
    exe = app_dir / "MacroFlow-v9.9.9-build999.exe"
    exe.write_bytes(b"MZ")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text("PyQt6\\QtCore.pyd\nQt6Core.dll\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_release_bundle.py"),
            "--exe",
            str(exe),
            "--app-dir",
            str(app_dir),
            "--archive-inventory",
            str(inventory),
            "--repository",
            "passdacom/macroflow",
            "--commit",
            "a" * 40,
            "--tag",
            "v9.9.9-build998",
            "--run-id",
            "12345",
            "--run-number",
            "998",
            "--source-date-epoch",
            "1785710000",
            "--output-dir",
            str(tmp_path / "release"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "project, executable, tag, and run number versions must match" in result.stderr


def test_pyinstaller_spec_and_bundle_gate_exclude_unneeded_qt_pdf(tmp_path: Path) -> None:
    spec = (ROOT / "build" / "macroflow-win.spec").read_text(encoding="utf-8").lower()
    assert "qt6pdf.dll" in spec
    assert "imageformats/qpdf.dll" in spec
    assert "opengl32sw.dll" in spec
    assert "collect(" in spec
    assert "exclude_binaries=true" in spec

    app_dir = tmp_path / "MacroFlow"
    app_dir.mkdir()
    exe = app_dir / f"MacroFlow-v{PROJECT_VERSION}-build999.exe"
    exe.write_bytes(b"MZ")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text(
        "PyQt6\\QtCore.pyd\nQt6Core.dll\nPyQt6\\Qt6\\bin\\Qt6Pdf.dll\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_release_bundle.py"),
            "--exe",
            str(exe),
            "--app-dir",
            str(app_dir),
            "--archive-inventory",
            str(inventory),
            "--repository",
            "passdacom/macroflow",
            "--commit",
            "a" * 40,
            "--tag",
            f"v{PROJECT_VERSION}-build999",
            "--run-id",
            "12345",
            "--run-number",
            "999",
            "--source-date-epoch",
            "1785710000",
            "--output-dir",
            str(tmp_path / "release"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "unreviewed Qt PDF payload" in result.stderr


def test_bundle_builder_rejects_unreviewed_qt_module(tmp_path: Path) -> None:
    app_dir = tmp_path / "MacroFlow"
    app_dir.mkdir()
    exe = app_dir / f"MacroFlow-v{PROJECT_VERSION}-build999.exe"
    exe.write_bytes(b"MZ")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text(
        "PyQt6\\QtCore.pyd\nQt6Core.dll\nQt6Multimedia.dll\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_release_bundle.py"),
            "--exe",
            str(exe),
            "--app-dir",
            str(app_dir),
            "--archive-inventory",
            str(inventory),
            "--repository",
            "passdacom/macroflow",
            "--commit",
            "a" * 40,
            "--tag",
            f"v{PROJECT_VERSION}-build999",
            "--run-id",
            "12345",
            "--run-number",
            "999",
            "--source-date-epoch",
            "1785710000",
            "--output-dir",
            str(tmp_path / "release"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "unreviewed Qt runtime module" in result.stderr

    inventory.write_text("PyQt6\\QtCore.pyd\nQt6Core.dll\nopengl32sw.dll\n", encoding="utf-8")
    native_result = subprocess.run(
        result.args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert native_result.returncode != 0
    assert "unreviewed native payload" in native_result.stderr

    inventory.write_text(
        "PyQt6\\QtCore.pyd\nQt6Core.dll\n"
        "PyQt6\\Qt6\\plugins\\multimedia\\windowsmediaplugin.dll\n",
        encoding="utf-8",
    )
    plugin_result = subprocess.run(
        result.args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert plugin_result.returncode != 0
    assert "unreviewed Qt plugin" in plugin_result.stderr

    surprise = app_dir / "_internal" / "surprise-native.dll"
    surprise.parent.mkdir()
    surprise.write_bytes(b"unexpected")
    inventory.write_text("PyQt6\\QtCore.pyd\nQt6Core.dll\n", encoding="utf-8")
    unknown_native_result = subprocess.run(
        result.args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert unknown_native_result.returncode != 0
    assert "unreviewed native payload" in unknown_native_result.stderr

    surprise.unlink()
    for name in (
        "api-ms-win-core-surprise.dll",
        "api-ms-win-crt-surprise-l9-9-9.dll",
    ):
        synthetic = app_dir / "_internal" / name
        synthetic.write_bytes(b"unexpected")
        api_set_result = subprocess.run(
            result.args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert api_set_result.returncode != 0
        assert "unreviewed native payload" in api_set_result.stderr
        synthetic.unlink()

    for name in (
        "evil _ctypes.pyd",
        "evil Qt6Core.dll",
        "Qt6Core.dll",
        "악성_ctypes.pyd",
        "api-ms-win-core-Kernel32-legacy-l1-1-1.dll",
    ):
        masquerade = app_dir / "_internal" / name
        masquerade.write_bytes(b"unexpected")
        masquerade_result = subprocess.run(
            result.args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert masquerade_result.returncode != 0
        assert "unreviewed native payload" in masquerade_result.stderr
        masquerade.unlink()

    misplaced_paths = (
        Path("_ctypes.pyd"),
        Path("libcrypto-3-x64.dll"),
        Path("python311.dll"),
        Path("api-ms-win-core-console-l1-1-0.dll"),
        Path("PyQt6/QtCore.pyd"),
        Path("PyQt6/Qt6/bin/Qt6Core.dll"),
        Path("PyQt6/Qt6/plugins/platforms/qwindows.dll"),
        Path("_internal/PyQt6/Qt6/bin/other/Qt6Core.dll"),
        Path("_internal/PyQt6/Qt6/bin/plugins/Qt6Widgets.dll"),
        Path("_internal/PyQt6/Qt6/bin/other/vcruntime140.dll"),
        Path("_internal/other/_ctypes.pyd"),
        Path("_internal/＿ctypes.pyd"),
        Path("_internal/helper.exe"),
    )
    for relative in misplaced_paths:
        misplaced = app_dir / relative
        misplaced.parent.mkdir(parents=True, exist_ok=True)
        misplaced.write_bytes(b"unexpected")
        misplaced_result = subprocess.run(
            result.args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert misplaced_result.returncode != 0
        assert "unreviewed native payload" in misplaced_result.stderr
        misplaced.unlink()

    mixed_case = app_dir / "_internal" / "_CTYPES.PYD"
    mixed_case.write_bytes(b"reviewed Windows path with alternate case")
    mixed_case_result = subprocess.run(
        result.args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert mixed_case_result.returncode == 0, mixed_case_result.stderr
    mixed_case.unlink()

    # The simultaneous collision probe requires a case-sensitive filesystem.
    # Windows is already covered above by the standalone Kelvin-sign API-set
    # payload, while NTFS may alias or enumerate the two names inconsistently.
    if sys.platform != "win32":
        qt_bin = app_dir / "_internal" / "PyQt6" / "Qt6" / "bin"
        reviewed_network = qt_bin / "Qt6Network.dll"
        kelvin_collision = qt_bin / "Qt6NetworK.dll"
        reviewed_network.write_bytes(b"reviewed")
        kelvin_collision.write_bytes(b"unreviewed Unicode collision")
        kelvin_output = tmp_path / "kelvin-release"
        kelvin_args = list(result.args)
        kelvin_args[kelvin_args.index("--output-dir") + 1] = str(kelvin_output)
        kelvin_result = subprocess.run(
            kelvin_args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert kelvin_result.returncode != 0
        assert "non-ASCII path" in kelvin_result.stderr
        assert not kelvin_output.exists()
        reviewed_network.unlink()
        kelvin_collision.unlink()


def test_windows_python_download_manifest_is_exact_and_pinned() -> None:
    manifest = json.loads((ROOT / "build" / "python-downloads.json").read_text(encoding="utf-8"))
    entry = manifest["cpython-3.11.15-windows-x86_64-none"]
    assert entry["url"].endswith(
        "/cpython-3.11.15%2B20260414-x86_64-pc-windows-msvc-install_only_stripped.tar.gz"
    )
    assert entry["sha256"] == (
        "71ffdf290e0483f0881e02518ecb9cedb449807856ae7dc76aa630e5acd00919"
    )
    assert entry["build"] == "20260414"


def test_release_workflow_publishes_gpl_bundle_and_verified_source_assets() -> None:
    workflow = _workflow()
    jobs = workflow["jobs"]  # type: ignore[index]
    build = jobs["build-exe"]  # type: ignore[index]
    release = jobs["release"]  # type: ignore[index]
    build_steps = _steps(build)
    release_steps = _steps(release)

    for job_name in ("lint-test", "build-exe"):
        commands = [step.get("run", "") for step in jobs[job_name]["steps"]]  # type: ignore[index,union-attr]
        assert "uv sync --locked --extra dev --extra ui-test --python 3.11.15" in commands

    assert "Build GPL distribution bundle" in build_steps
    bundle_command = str(build_steps["Build GPL distribution bundle"]["run"])
    bundle_env = build_steps["Build GPL distribution bundle"]["env"]
    assert isinstance(bundle_env, dict)
    assert bundle_env["PYTHON_BUILD_SOURCE_SHA256"] == (
        "8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c"
    )
    assert "tools/build_release_bundle.py" in bundle_command
    assert "pyi-archive_viewer" in bundle_command
    assert "--app-dir" in bundle_command
    assert "Get-ChildItem 'dist/MacroFlow' -Recurse" in bundle_command
    assert "--commit $env:GITHUB_SHA" in bundle_command
    assert "--source-date-epoch $sourceDateEpoch" in bundle_command
    assert "PYTHON_BUILD_SOURCE_SHA256" in bundle_command
    assert "Get-FileHash -Algorithm SHA256 $path" in bundle_command
    assert "source.extractfile(member).read()" in bundle_command
    assert "licenses/libffi-MIT.txt" in bundle_command
    assert "licenses/bzip2-1.0.8.txt" in bundle_command
    assert "checked-in license differs" in bundle_command
    assert "codeload.github.com/astral-sh/python-build-standalone/tar.gz/7af98d60e411de479ab16f5537efc7184dffc25a" in bundle_command
    assert "Copy-Item $source.Path 'release/'" in bundle_command

    assert "Verify replaceable Qt runtime layout" in build_steps
    qt_layout_command = str(build_steps["Verify replaceable Qt runtime layout"]["run"])
    assert "Qt6Core.dll" in qt_layout_command
    assert "pyi-archive_viewer" in qt_layout_command

    upload = build_steps["Upload GPL release artifact"]
    assert upload["with"]["path"] == "release/"  # type: ignore[index]

    release_step = release_steps["Create release"]
    assert release_step["with"]["files"] == "release/*"  # type: ignore[index]
    body = str(release_step["with"]["body"])  # type: ignore[index]
    assert "GPLv3" in body
    assert "corresponding source" in body.lower()
    assert "github.sha" in body
    assert "python-build-standalone" in body
    assert "reviewed runtime companion source archives" in body
