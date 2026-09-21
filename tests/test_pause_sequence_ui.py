"""Real offscreen full/selected sequence pause labels with mocked native I/O."""
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("selected", [False, True], ids=["whole", "selected-4-7"])
def test_sequence_pause_labels(tmp_path, selected):
    env = dict(os.environ)
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME",
                "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "TMPDIR", "TEMP", "TMP"):
        folder = tmp_path / key
        folder.mkdir(mode=0o700)
        env[key] = str(folder)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    script = r'''
import os, sys, types, threading, time
from pathlib import Path
from unittest.mock import MagicMock
w32 = types.ModuleType("macroflow.win32")
w32.__path__ = [str(Path(os.environ["PYTHONPATH"]) / "macroflow/win32")]
w32.__getattr__ = lambda name: MagicMock(name=name)
for name in ("send_key", "send_mouse_move", "send_mouse_button", "send_mouse_wheel",
             "send_paste", "set_clipboard_text", "start_hook", "stop_hook",
             "start_emergency_hook", "stop_emergency_hook"):
    setattr(w32, name, MagicMock(name=name))
w32.get_logical_screen_size = lambda: (1920, 1080)
sys.modules["macroflow.win32"] = w32
from PyQt6.QtWidgets import QApplication, QMessageBox
from macroflow.ui.main_window import MainWindow
from macroflow.sequence_model import MacroFileItem, WaitItem
from macroflow.types import KeyEvent, WaitEvent, MacroData, MacroMeta, MacroSettings
from macroflow.macro_file import save
from macroflow import player
app = QApplication([])
window = MainWindow()
held, release, unheld = threading.Event(), threading.Event(), threading.Event()
original = player._execute_event
def execute(event, settings, state):
    if event.id == "ordinary":
        unheld.set()
    original(event, settings, state)
    if event.id == "down":
        held.set()
        assert release.wait(3)
player._execute_event = execute
window._sequencer._items = [WaitItem(step_id=f"w{i}", duration_ms=0) for i in range(10)]
events = [
    KeyEvent(id="down", type="key_down", timestamp_ns=0, key="ctrl", vk_code=17),
    KeyEvent(id="up", type="key_up", timestamp_ns=0, key="ctrl", vk_code=17),
    WaitEvent(id="ordinary", type="wait", timestamp_ns=0, duration_ms=1000)]
path = Path.cwd() / "synthetic.json"
save(MacroData(meta=MacroMeta(version="1.0", app_version="1.11.0", created_at="",
    screen_width=1920, screen_height=1080, dpi_scale=1.0), settings=MacroSettings(),
    events=events, raw_events=[]), str(path))
window._sequencer._items[3] = MacroFileItem(step_id="input", path=path)
window._sequencer._refresh_all()
QMessageBox.question = lambda *a: QMessageBox.StandardButton.Yes
QMessageBox.warning = lambda *a: None
def until(predicate):
    deadline = time.monotonic() + 3
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.001)
    assert predicate()
try:
    window._toggle_sequencer(selected_rows=[3,4,5,6] if selected else None)
    session = window._sequencer._engine
    until(held.is_set)
    window._toggle_pause()
    window._poll_state()
    assert session.pause_state() == "requested"
    assert window._sb_state.text() == "일시중지 요청됨 — 입력 해제 대기"
    assert w32.send_key.call_count == 1
    release.set()
    until(lambda: session.pause_state() == "paused")
    window._poll_state()
    assert window._sb_state.text() == "플로우 일시중지"
    assert w32.send_key.call_count == 2
    window._toggle_pause()
    assert session.pause_state() == "running"
    assert window._sb_state.text() == "플로우 실행 중"
    assert unheld.wait(2)
    window._toggle_pause()
    assert session.pause_state() == "paused", "ordinary unheld wait pauses immediately"
    window._poll_state()
    assert window._sb_state.text() == "플로우 일시중지"
    window._toggle_pause()
    until(lambda: not session.is_running())
    app.processEvents()
    assert w32.send_key.call_count == 2
finally:
    release.set()
    if window._sequencer._engine is not None:
        window._sequencer._engine.stop()
    player.stop()
    app.processEvents()
    window.close()
'''
    result = subprocess.run([sys.executable, "-c", f"selected = {selected!r}\n" + script],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
