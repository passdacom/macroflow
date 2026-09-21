"""Run the real persistence harness, never a replacement implementation."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "tools/rdp_sequencer_flow_smoke.py"


def _environment(tmp_path):
    env = dict(os.environ)
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME",
                "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "TMPDIR", "TEMP", "TMP"):
        folder = tmp_path / f"격리-{key}"
        folder.mkdir(mode=0o700)
        env[key] = str(folder)
    env.update(QT_QPA_PLATFORM="offscreen", PYTHONPATH=str(REPO / "src"),
               PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    return env


def test_actual_sequencer_smoke_is_bounded(tmp_path):
    env = _environment(tmp_path)
    # Windows redirected consoles may have a non-UTF8 default encoding.
    env["PYTHONIOENCODING"] = "ascii"
    result = subprocess.run(
        [sys.executable, str(HARNESS), "--report", "보고서.json"],
        cwd=tmp_path, env=env,
        capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tmp_path / "보고서.json").read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert all(report["assertions"].values())
    assert not Path(report["work_dir"]).exists()
    assert report["assertions"]["persisted_merge_closure"]
    assert report["assertions"]["source_documents_unchanged"]
    assert report["assertions"]["synthetic_releases"]
    assert report["assertions"]["no_held_state"]


@pytest.mark.parametrize("fault", ["critical", "warning", "question", "native", "dot-path"])
def test_smoke_fails_fast_and_restores_process_state(tmp_path, fault):
    script = r'''
import json
import os
import runpy
import sys
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication, QMessageBox

harness = runpy.run_path(sys.argv[1])
widget = harness["MacroSequencerWidget"]
win32 = harness["win32"]
app = QApplication([])
cwd = Path.cwd()
original_native = win32.send_key
original_dialog = QMessageBox.__dict__["critical"]
original_load = widget._load_flow_from_path
fault = sys.argv[2]

def faulty_load(self, path):
    assert Path.cwd() != cwd, "exercise failure inside temporary cwd"
    if fault == "dot-path":
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["nodes"]["macro_000"]["macro_path"] = "./macros/../macros/first.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return original_load(self, path)
    if fault == "native":
        return win32.send_key(65, True)
    return getattr(QMessageBox, fault)(self, "injected", "unexpected")

with patch.object(widget, "_load_flow_from_path", faulty_load):
    try:
        harness["run_smoke"]()
    except RuntimeError as exc:
        expected = "Native I/O is forbidden" if fault == "native" else "Unexpected smoke dialog"
        assert expected in str(exc), str(exc)
        if fault == "dot-path":
            assert "정규 시퀀서 문서" in str(exc)
    else:
        raise AssertionError("unexpected operation was silently accepted")
assert Path.cwd() == cwd, "cwd leaked"
assert win32.send_key is original_native, "native guard leaked"
assert QMessageBox.__dict__["critical"] is original_dialog, "dialog guard leaked"
assert not list(Path(os.environ["TMPDIR"]).glob("macroflow-sequencer-smoke-*"))
print("FAIL_FAST_RESTORED")
'''
    result = subprocess.run(
        [sys.executable, "-c", script, str(HARNESS), fault],
        cwd=tmp_path, env=_environment(tmp_path),
        capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FAIL_FAST_RESTORED" in result.stdout
