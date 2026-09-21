"""Actual offscreen QAction regressions; native boundaries replaced before import."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

SETUP = '''
import sys, types, os
from pathlib import Path
from unittest.mock import MagicMock
w32 = types.ModuleType("macroflow.win32")
w32.__path__ = [str(Path(os.environ["PYTHONPATH"]) / "macroflow/win32")]
w32.__getattr__ = lambda name: MagicMock(name=name)
w32.get_logical_screen_size = lambda: (1920, 1080)
sys.modules["macroflow.win32"] = w32
from PyQt6.QtWidgets import QApplication, QMenu, QDialog, QInputDialog
from PyQt6.QtCore import QPoint
from macroflow.ui.editor import EventEditorWidget
from macroflow.types import MacroData, MacroMeta, MacroSettings, KeyEvent
app = QApplication([])
def macro():
    return MacroData(meta=MacroMeta(version="1.0", app_version="1.11.0", created_at="",
        screen_width=1920, screen_height=1080, dpi_scale=1.0), settings=MacroSettings(),
        events=[KeyEvent(id="down", type="key_down", timestamp_ns=0, key="a", vk_code=65),
                KeyEvent(id="up", type="key_up", timestamp_ns=1000000, key="a", vk_code=65)], raw_events=[])
def action(menu, text):
    return next(a for a in menu.actions() if text in a.text())
'''


def run_ui(tmp_path, script):
    env = dict(os.environ)
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME",
                "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "TMPDIR", "TEMP", "TMP"):
        folder = tmp_path / key
        folder.mkdir(mode=0o700)
        env[key] = str(folder)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run([sys.executable, "-B", "-c", SETUP + script],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr


def test_delay_action_edits_without_inserting_and_click_add_still_inserts(tmp_path):
    run_ui(tmp_path, '''
editor = EventEditorWidget()
editor.load_macro(macro())
editor._table.selectRow(0)
QInputDialog.getInt = lambda *a, **kw: (250, True)
QDialog.exec = lambda self: QDialog.DialogCode.Accepted
QMenu.exec = lambda self, *a: action(self, "재생 대기 설정").trigger()
editor._context_menu(QPoint())
assert [e.type for e in editor.current_macro().events] == ["key_down", "key_up"]
assert editor.current_macro().events[0].delay_override_ms == 250
editor._act_undo.trigger()
assert editor.current_macro().events == macro().events
editor._table.selectRow(0)
QMenu.exec = lambda self, *a: action(self, "클릭 추가").trigger()
editor._start_f6_capture = lambda callback: callback(.5, .5, "#FFFFFF")
editor._context_menu(QPoint())
assert [e.type for e in editor.current_macro().events] == ["key_down", "key_up", "mouse_down", "mouse_up"]
''')


@pytest.mark.parametrize("stage", ["menu", "dialog"])
@pytest.mark.parametrize("invalidate", ["disabled", "generation"])
def test_delay_action_rejects_disabled_or_stale_commit(tmp_path, stage, invalidate):
    run_ui(tmp_path, f'''
editor = EventEditorWidget()
editor.load_macro(macro())
editor._table.selectRow(0)
def invalidate():
    if {invalidate!r} == "disabled": editor.setEnabled(False)
    else: editor.load_macro(macro())
def get_int(*a, **kw):
    if {stage!r} == "dialog": invalidate()
    return 250, True
QInputDialog.getInt = get_int
QDialog.exec = lambda self: QDialog.DialogCode.Accepted
def menu_exec(self, *args):
    if {stage!r} == "menu": invalidate()
    action(self, "재생 대기 설정").trigger()
QMenu.exec = menu_exec
editor._context_menu(QPoint())
assert editor.current_macro().events == macro().events
assert not editor._undo_stack
''')


def test_context_play_status_uses_actual_raw_range_not_toolbar_rows(tmp_path):
    run_ui(tmp_path, '''
import dataclasses, threading
from macroflow.ui.main_window import MainWindow
from macroflow.ui import range_preparation
from macroflow.types import MouseMoveEvent
from macroflow import player
window = MainWindow()
data = macro()
data.events += [MouseMoveEvent(id="hidden", type="mouse_move", timestamp_ns=2000000,
    x_ratio=.1, y_ratio=.1)]
data.events += [dataclasses.replace(e, id="second-" + e.id, key="b", vk_code=66,
    timestamp_ns=e.timestamp_ns + 3000000) for e in macro().events]
window._macro = data
window._editor.load_macro(data)
window._update_range_spinboxes()
window._range_start_spin.setValue(1)
window._range_end_spin.setValue(1)
assert window._calc_event_range() == (0, 2), window._calc_event_range()
assert window._editor.get_event_range_for_rows(2, 2) == (3, 5), window._editor._rows
range_preparation.external_target_ready = lambda **kw: True
QDialog.exec = lambda self: QDialog.DialogCode.Accepted
seen, started, finished = [], threading.Event(), threading.Event()
def play(data, **kw):
    seen.append(kw["event_range"])
    kw["on_complete"]()
    started.set()
    return player.PlaybackSession()
player.play = play
window._sig_play_complete.connect(lambda *a: finished.set())
window._editor._table.selectRow(1)
QMenu.exec = lambda self, *a: action(self, "이 이벤트만 실행").trigger()
window._editor._context_menu(QPoint())
assert started.wait(2)
assert seen == [(3, 5)], seen
assert "[원본 이벤트 4~5]" in window._sb_state.text(), window._sb_state.text()
assert window._range_start_spin.value() == 1 and window._range_end_spin.value() == 1
window._stop_playback()
from PyQt6.QtWidgets import QMessageBox
QMessageBox.question = lambda *a: QMessageBox.StandardButton.Discard
window.close()
''')
