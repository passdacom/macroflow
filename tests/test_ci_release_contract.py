"""GitHub Actions release safety contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(".github/workflows/build.yml")
PINNED_ACTIONS = {
    "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
    "astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78",
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
    "softprops/action-gh-release@3bb12739c298aeb8a4eeaf626c5b8d85266b0e65",
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
        assert "uv sync --locked --extra dev --extra ui-test --python 3.11" in commands

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


def test_release_requires_manual_dispatch_and_publishes_provenance() -> None:
    workflow = _workflow()
    release = workflow["jobs"]["release"]
    assert "workflow_dispatch" in workflow["on"]
    assert release["if"] == (
        "github.ref == 'refs/heads/main' && github.event_name == 'workflow_dispatch'"
    )
    assert release["needs"] == "build-exe"
    release_step = _steps(release)["Create release"]
    assert release_step["with"]["files"] == "dist/MacroFlow-v*"
    assert "github.sha" in release_step["with"]["body"]
    assert ".sha256" in release_step["with"]["body"]


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
