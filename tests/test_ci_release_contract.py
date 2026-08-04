"""GitHub Actions release safety contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(".github/workflows/build.yml")
PINNED_ACTIONS = {
    "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
    "astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78",
    "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f",
    "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
    "softprops/action-gh-release@3d0d9888cb7fd7b750713d6e236d1fcb99157228",
}


def _workflow() -> dict[str, Any]:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML follows YAML 1.1 and parses the GitHub key `on` as boolean true.
    if True in workflow and "on" not in workflow:
        workflow["on"] = workflow.pop(True)
    return workflow


def _steps(job: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step.get("name", step.get("uses", "")): step for step in job["steps"]}


def test_ci_uses_locked_dependencies_on_linux_and_windows() -> None:
    jobs = _workflow()["jobs"]
    for job_name in ("lint-test", "build-exe"):
        commands = [step.get("run", "") for step in jobs[job_name]["steps"]]
        assert "uv sync --locked --extra dev --extra ui-test --python 3.11.15" in commands

    windows_python = _steps(jobs["build-exe"])["Set up Python 3.11"]["run"]
    assert "--python-downloads-json-url" in windows_python
    assert "build/python-downloads.json" in windows_python
    assert jobs["build-exe"]["env"]["UV_PYTHON_DOWNLOADS_JSON_URL"] == (
        "${{ github.workspace }}/build/python-downloads.json"
    )

    validation = _steps(jobs["lint-test"])["Validate GitHub Actions workflow"]["run"]
    assert '$(go env GOPATH)/bin/actionlint" .github/workflows/build.yml' in validation
    assert "zizmor --min-severity medium" in validation


def test_windows_job_runs_tests_before_build_and_owns_smoke_process_tree() -> None:
    build_steps = _workflow()["jobs"]["build-exe"]["steps"]
    names = [step.get("name", "") for step in build_steps]
    assert names.index("Run pytest on Windows") < names.index("Build EXE")
    smoke = _steps(_workflow()["jobs"]["build-exe"])["Smoke packaged EXE"]["run"]
    assert "Get-CimInstance Win32_Process" in smoke
    assert "Get-Process -Id @($ownedIds)" in smoke
    assert "$_.MainWindowTitle -like 'MacroFlow*'" in smoke
    assert "taskkill.exe /PID $process.Id /T /F" in smoke
    assert "Get-Process | Where-Object" not in smoke


def test_windows_job_proves_lgpl_library_replacement_without_mutating_release() -> None:
    build_steps = _workflow()["jobs"]["build-exe"]["steps"]
    names = [step.get("name", "") for step in build_steps]
    step_name = "Smoke modified replaceable Qt library"
    assert names.index("Smoke packaged inline sequence codec") < names.index(step_name)
    assert names.index(step_name) < names.index("Build GPL distribution bundle")

    smoke = _steps(_workflow()["jobs"]["build-exe"])[step_name]["run"]
    assert "Qt6Core.dll" in smoke
    assert "TimeDateStamp" in smoke
    assert "$modifiedHash -eq $originalHash" in smoke
    assert "MainWindowTitle -like 'MacroFlow*'" in smoke
    assert "finally" in smoke
    assert "Wait-Process -Id @($ownedIds)" in smoke
    assert "$restoreDeadline" in smoke
    assert "Start-Sleep -Milliseconds 200" in smoke
    assert "$restoredHash -ne $originalHash" in smoke


def test_release_requires_manual_dispatch_and_publishes_provenance() -> None:
    workflow = _workflow()
    release = workflow["jobs"]["release"]
    assert "workflow_dispatch" in workflow["on"]
    assert release["if"] == (
        "github.ref == 'refs/heads/main' && github.event_name == 'workflow_dispatch'"
    )
    assert release["needs"] == "build-exe"
    release_step = _steps(release)["Create release"]
    assert release_step["with"]["files"] == "release/*"
    assert release_step["with"]["draft"] is True
    assert release_step["with"]["make_latest"] is False
    assert release_step["with"]["overwrite_files"] is False
    assert release_step["with"]["target_commitish"] == "${{ github.sha }}"
    assert "github.sha" in release_step["with"]["body"]
    assert ".sha256" in release_step["with"]["body"]
    assert "GPLv3" in release_step["with"]["body"]
    assert "corresponding source" in release_step["with"]["body"].lower()

    names = [step.get("name", "") for step in release["steps"]]
    assert names.index("Preflight release tag") < names.index("Create release")
    assert names.index("Create release") < names.index("Verify draft release assets")
    assert names.index("Verify draft release assets") < names.index("Publish verified release")
    verification = _steps(release)["Verify draft release assets"]["run"]
    assert "gh release download" in verification
    assert "gh release view" in verification
    assert "isDraft" in verification
    assert "sha256sum -c" in verification
    assert "EXPECTED_SHA" in verification
    assert "resolve_tag_commit" in verification
    publication = _steps(release)["Publish verified release"]["run"]
    assert "gh release edit" in publication
    assert "--draft=false" in publication
    assert "--latest" in publication
    assert "releases/latest" in publication
    assert "EXPECTED_SHA" in publication
    assert "digest" in publication

    preflight = _steps(release)["Preflight release tag"]["run"]
    assert "releases/tags/$TAG" in preflight
    assert "git/ref/tags/$TAG" in preflight
    assert "HTTP 404" in preflight


def test_actions_are_sha_pinned_and_tokens_are_least_privilege() -> None:
    workflow = _workflow()
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["release"]["permissions"] == {"contents": "write"}

    used_actions = {
        step["uses"].split(" #", maxsplit=1)[0]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "uses" in step
    }
    assert used_actions == PINNED_ACTIONS

    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if step.get("uses", "").startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] is False
