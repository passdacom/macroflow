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
WORKFLOW = ROOT / ".github" / "workflows" / "build.yml"
LICENSE_FILES = {
    "GPL-3.0-only.txt",
    "LGPL-3.0-only.txt",
    "BSD-2-Clause-PyQt6-sip.txt",
    "PSF-2.0-Python.txt",
    "MPL-2.0-python-build-standalone.txt",
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


def test_runtime_license_bundle_and_notices_are_checked_in() -> None:
    license_dir = ROOT / "licenses"
    assert {path.name for path in license_dir.iterdir() if path.is_file()} == LICENSE_FILES

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
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
    ):
        assert required in notices


def test_bundle_builder_packages_exe_source_pointer_notices_and_spdx(tmp_path: Path) -> None:
    app_dir = tmp_path / "MacroFlow"
    runtime_dir = app_dir / "_internal" / "PyQt6" / "Qt6" / "bin"
    runtime_dir.mkdir(parents=True)
    exe = app_dir / "MacroFlow-v1.6.1-build999.exe"
    exe.write_bytes(b"MZ\x00macroflow-test")
    (runtime_dir / "Qt6Core.dll").write_bytes(b"qt-runtime")
    inventory = tmp_path / "inventory.txt"
    inventory.write_text("PyQt6\\QtCore.pyd\nPyQt6\\Qt6\\bin\\Qt6Core.dll\n", encoding="utf-8")
    output = tmp_path / "release"
    commit = "a" * 40
    tag = "v1.6.1-build999"

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
    bundle = output / "MacroFlow-v1.6.1-build999-GPL.zip"
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
        prefix = "MacroFlow-v1.6.1-build999/"
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
    assert package_licenses["PyQt6-Qt6"] == "LGPL-3.0-only"
    assert package_licenses["PyQt6-sip"] == "BSD-2-Clause"
    assert package_licenses["Python"] == "PSF-2.0"
    assert package_licenses["python-build-standalone"] == "MPL-2.0"
    assert package_licenses["MacroFlow Windows Distribution"] == "GPL-3.0-only"
    assert package_licenses["PyInstaller Bootloader"] == "NOASSERTION"
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
    provenance_text = provenance.read_text(encoding="ascii")
    assert "python_build_source_commit=7af98d60e411de479ab16f5537efc7184dffc25a" in provenance_text
    assert (
        "python_build_source_sha256=8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c"
        in provenance_text
    )


def test_bundle_builder_rejects_non_full_commit(tmp_path: Path) -> None:
    app_dir = tmp_path / "MacroFlow"
    app_dir.mkdir()
    exe = app_dir / "MacroFlow-v1.6.1-build999.exe"
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
            "v1.6.1-build999",
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
    assert "collect(" in spec
    assert "exclude_binaries=true" in spec

    app_dir = tmp_path / "MacroFlow"
    app_dir.mkdir()
    exe = app_dir / "MacroFlow-v1.6.1-build999.exe"
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
            "v1.6.1-build999",
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


def test_release_workflow_publishes_only_the_gpl_bundle_and_compliance_sidecars() -> None:
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
    assert "Get-FileHash -Algorithm SHA256 $pythonBuildSource" in bundle_command
    assert "codeload.github.com/astral-sh/python-build-standalone/tar.gz/7af98d60e411de479ab16f5537efc7184dffc25a" in bundle_command
    assert "Copy-Item $pythonBuildSource 'release/'" in bundle_command

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
