"""Close during a real Qt flow confirmation must invalidate the pending start."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("selected", [False, True], ids=["whole-flow", "selected-4-7"])
@pytest.mark.parametrize("close_choice", ["accept", "editor-cancel", "flow-cancel"])
def test_close_invalidates_pending_flow_start(tmp_path, selected, close_choice):
    env = dict(os.environ)
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME",
                 "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "TMPDIR", "TEMP", "TMP"):
        directory = tmp_path / name
        directory.mkdir(mode=0o700)
        env[name] = str(directory)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    script = r'''
import copy
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# Install the platform boundary BEFORE importing any MacroFlow module.
w32 = types.ModuleType("macroflow.win32")
w32.__path__ = [str(Path(os.environ["PYTHONPATH"]) / "macroflow/win32")]
w32.__getattr__ = lambda name: MagicMock(name=name)
inputs = {}
for name in ("send_key", "send_mouse_move", "send_mouse_button", "send_mouse_wheel",
             "send_paste", "set_clipboard_text", "send_mouse_drag", "start_hook",
             "stop_hook", "start_emergency_hook", "stop_emergency_hook"):
    inputs[name] = MagicMock(name=name)
    setattr(w32, name, inputs[name])
w32.get_logical_screen_size = lambda: (1920, 1080)
w32.ratio_to_pixel = lambda x, y: (int(x * 1920), int(y * 1080))
w32.pixel_to_ratio = lambda x, y: (x / 1920, y / 1080)
sys.modules["macroflow.win32"] = w32

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QCloseEvent
from macroflow.ui.main_window import MainWindow
import macroflow.ui.main_window as main_module
from macroflow.sequence_model import InlineActionItem, WaitItem
from macroflow.sequence_run import SequenceRunSession
from macroflow.types import MacroData, MacroMeta, MacroSettings, TextInputEvent
from macroflow import player

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
window = MainWindow()
# Exercise Windows hook ownership branches without loading native APIs.
main_module.sys = types.SimpleNamespace(platform="win32")
window._sequencer._items = [WaitItem(step_id=f"w{i}", duration_ms=0) for i in range(10)]
window._sequencer._items[3] = InlineActionItem(step_id="text", label="test", events=[
    TextInputEvent(id="t", type="text_input", timestamp_ns=0, text="QA-ONLY")])
window._sequencer._refresh_all()
window._sequencer._flow_repeat_mode.setCurrentIndex(2)
if close_choice == "editor-cancel":
    window._macro = MacroData(meta=MacroMeta(version="1.0", app_version="1.11.0",
        created_at="", screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(), events=[], raw_events=[])
    window._saved_macro = None
elif close_choice == "flow-cancel":
    window._sequencer._set_dirty(True)
before_items = copy.deepcopy(window._sequencer._items)
before_macro = copy.deepcopy(window._macro)
# No worker can be spawned, even on the failing baseline.
starts = []
SequenceRunSession.start = lambda self, flow: starts.append(flow)
player.play = MagicMock(name="player.play")
questions = []
closed = []
reentries = []
def confirm(parent, title, *args):
    questions.append(title)
    if title != "플로우 실행 범위":
        return QMessageBox.StandardButton.Cancel
    assert window._state == "flow_preparing"
    event = QCloseEvent()
    window.closeEvent(event)
    closed.append(event.isAccepted())
    # A queued start while the old modal stack unwinds must remain blocked.
    window._toggle_sequencer(selected_rows=[3, 4, 5, 6] if selected else None)
    reentries.append(len(questions))
    return QMessageBox.StandardButton.Yes
QMessageBox.question = confirm
QMessageBox.warning = lambda *args: None
window._toggle_sequencer(selected_rows=[3, 4, 5, 6] if selected else None)
assert closed == [close_choice == "accept"], closed
assert not starts, "stale modal acceptance started a flow after close"
assert not player.play.called
for name in ("send_key", "send_mouse_move", "send_mouse_button", "send_mouse_wheel",
             "send_paste", "set_clipboard_text", "send_mouse_drag", "start_hook"):
    assert not inputs[name].called, name
assert window._flow_preparation_cancelled
assert window._state == "idle"
assert window._sequencer._start_allowed is None
assert window._sequencer._engine is None
assert not window._sequencer.is_running()
assert not window._overlay.isVisible()
assert inputs["start_emergency_hook"].call_count == 1
assert inputs["stop_emergency_hook"].call_count == 1
assert questions.count("플로우 실행 범위") == 1, questions
assert reentries == [len(questions)]
assert window._sequencer._items == before_items
assert window._macro == before_macro
if close_choice != "accept":
    assert window._editor_is_dirty() if close_choice == "editor-cancel" else window._sequencer.is_dirty()
    # Once the cancelled modal frame has unwound a fresh explicit start is valid.
    QMessageBox.question = lambda *args: QMessageBox.StandardButton.Yes
    window._toggle_sequencer(selected_rows=[3, 4, 5, 6] if selected else None)
    assert len(starts) == 1
    assert not window._flow_preparation_cancelled
    window._stop_sequencer()
    window._macro = None
    window._sequencer._set_dirty(False)
    window.close()
print("PASS: close outcome, stale Yes/re-entry, no input/worker, hook cleanup, dirty preservation")
'''
    result = subprocess.run(
        [sys.executable, "-c", f"selected = {selected!r}\nclose_choice = {close_choice!r}\n" + script],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
