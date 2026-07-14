from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "run_rdp_gui_smoke.ps1"


def _script_text() -> str:
    return _SCRIPT.read_text(encoding="utf-8")


def test_runner_redirects_stdout_and_stderr_without_powershell_error_records():
    script = _script_text()

    assert "Start-Process" in script
    assert "-ArgumentList @(" in script
    assert "-RedirectStandardOutput" in script
    assert "-RedirectStandardError" in script
    assert "Start-Process \\" not in script
    assert "Tee-Object" not in script
    assert "2>&1 | Tee-Object" not in script


def test_runner_preserves_clipboard_summary_contract():
    script = _script_text()

    assert 'GUI_SMOKE_EXIT=$exit' in script
    assert 'Set-Clipboard -Value $txt' in script
    assert 'Write-Host $txt' in script
