from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_qt(code: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_main_window_has_quick_run_as_the_fourth_tab() -> None:
    result = _run_qt(
        """
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QScrollArea
from macroflow.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
with TemporaryDirectory() as directory:
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    with patch.object(MainWindow, "_restore_settings", lambda self: None):
        window = MainWindow()
    assert [window._tabs.tabText(i) for i in range(window._tabs.count())] == [
        "매크로 에디터", "시퀀서", "즐겨찾기", "빠른 실행"
    ]
    assert len(window._quick_run._name_edits) == 5
    scroll = window._quick_run.findChild(QScrollArea, "quick-run-scroll")
    assert scroll is not None
    window.resize(1100, 720)
    window._tabs.setCurrentWidget(window._quick_run)
    window.show()
    app.processEvents()
    assert scroll.height() > 450
    window.close()
"""
    )
    assert result.returncode == 0, result.stderr


def test_quick_run_widget_emits_five_slots_and_hotkeys_on_apply() -> None:
    result = _run_qt(
        """
from pathlib import Path
from tempfile import TemporaryDirectory
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QApplication
from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
from macroflow.quick_run import default_quick_run_slots
from macroflow.ui.quick_run import QuickRunWidget

app = QApplication.instance() or QApplication([])
with TemporaryDirectory() as directory:
    macro = Path(directory) / "step.json"
    macro.write_text("{}", encoding="utf-8")
    widget = QuickRunWidget(default_quick_run_slots(), DEFAULT_HOTKEY_CONFIG)
    captured = []
    widget.configuration_requested.connect(lambda slots, bindings: captured.append((slots, bindings)))
    widget._name_edits[0].setText("공통 전처리")
    widget._path_edits[0].setText(str(macro))
    widget._hotkey_edits[0].setKeySequence(QKeySequence("Ctrl+Shift+1"))
    widget._apply_changes()
    slots, bindings = captured[-1]
    assert len(slots) == 5
    assert slots[0].name == "공통 전처리"
    assert slots[0].macro_path == macro.resolve(strict=False)
    assert bindings["quick_run.slot_1"] == "Ctrl+Shift+1"
    widget.close()
"""
    )
    assert result.returncode == 0, result.stderr


def test_hotkey_settings_dialog_includes_quick_run_shortcuts() -> None:
    result = _run_qt(
        """
from PyQt6.QtWidgets import QApplication
from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
from macroflow.ui.hotkey_settings_dialog import HotkeySettingsDialog

app = QApplication.instance() or QApplication([])
dialog = HotkeySettingsDialog(DEFAULT_HOTKEY_CONFIG)
assert [f"quick_run.slot_{index}" in dialog._edits for index in range(1, 6)] == [True] * 5
assert dialog._edits["quick_run.slot_1"].keySequence().toString() == "Ctrl+Alt+1"
dialog.close()
"""
    )
    assert result.returncode == 0, result.stderr


def test_quick_run_hotkey_editor_suspends_dispatch_until_focus_leaves() -> None:
    result = _run_qt(
        """
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from macroflow.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
with patch.object(MainWindow, "_restore_settings", lambda self: None):
    window = MainWindow()
runtime = Mock()
runtime.initialized = True
runtime.globally_registered = True
runtime.set_quick_run_enabled.return_value.success = True
window._hotkey_runtime = runtime
window.show()
window._tabs.setCurrentWidget(window._quick_run)
app.processEvents()

editor = window._quick_run._hotkey_edits[0]
editor.setFocus()
app.processEvents()
runtime.set_quick_run_enabled.assert_called_once_with(False)
assert window._quick_run_hotkey_editing

with patch.object(window, "_run_quick_slot") as run:
    window._dispatch_hotkey_action("quick_run.slot_1")
run.assert_not_called()

window._quick_run._name_edits[0].setFocus()
app.processEvents()
app.processEvents()
runtime.set_quick_run_enabled.assert_called_with(True)
assert not window._quick_run_hotkey_editing
window.close()
"""
    )
    assert result.returncode == 0, result.stderr


def test_invalid_quick_run_hotkey_is_rejected_before_slot_persistence() -> None:
    result = _run_qt(
        """
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from macroflow.quick_run import default_quick_run_slots
from macroflow.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
with TemporaryDirectory() as directory:
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    with patch.object(MainWindow, "_restore_settings", lambda self: None):
        window = MainWindow()
    bindings = {"quick_run.slot_1": ""}
    with patch("macroflow.ui.main_window.save_quick_run_slots") as save_slots, \
         patch("macroflow.ui.main_window.QMessageBox.warning") as warning:
        window._apply_quick_run_configuration(default_quick_run_slots(), bindings)
    save_slots.assert_not_called()
    warning.assert_called_once()
    assert "단축키" in warning.call_args.args[2]
    window.close()
"""
    )
    assert result.returncode == 0, result.stderr


def test_quick_run_drops_busy_calls_and_fails_closed_for_corrupt_files() -> None:
    result = _run_qt(
        """
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from macroflow.quick_run import QuickRunSlot, default_quick_run_slots
from macroflow.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
with TemporaryDirectory() as directory:
    corrupt = Path(directory) / "broken.json"
    corrupt.write_text("not-json", encoding="utf-8")
    slots = list(default_quick_run_slots())
    slots[0] = QuickRunSlot(index=1, name="위험 슬롯", macro_path=corrupt)
    with patch.object(MainWindow, "_restore_settings", lambda self: None):
        window = MainWindow()
    window._quick_run_slots = tuple(slots)

    window._state = "playing"
    with patch.object(window, "_start_playback") as start:
        window._run_quick_slot(1)
    start.assert_not_called()
    assert "실행 안 함" in window._sb_state.text()

    window._state = "idle"
    with patch.object(window, "_bring_to_front_for_prompt"), \
         patch("macroflow.ui.main_window.QMessageBox.warning") as warning, \
         patch.object(window, "_start_playback") as start:
        window._run_quick_slot(1)
    start.assert_not_called()
    warning.assert_called_once()
    assert "불러오지 못했습니다" in warning.call_args.args[2]
    window.close()
"""
    )
    assert result.returncode == 0, result.stderr


def test_quick_run_loads_a_fresh_macro_without_replacing_the_editor_macro() -> None:
    result = _run_qt(
        """
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from macroflow import macro_file
from macroflow.quick_run import QuickRunSlot, default_quick_run_slots
from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
from macroflow.ui.main_window import MainWindow

app = QApplication.instance() or QApplication([])
with TemporaryDirectory() as directory:
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    path = Path(directory) / "slot.json"
    meta = MacroMeta(
        version="1.0", app_version="test", created_at="2026-08-03T00:00:00",
        screen_width=1920, screen_height=1080, dpi_scale=1.0,
    )
    slot_macro = MacroData(
        meta=meta, settings=MacroSettings(), raw_events=[],
        events=[WaitEvent(id="slot-wait", type="wait", timestamp_ns=0, duration_ms=1)],
    )
    macro_file.save(slot_macro, str(path))
    with patch.object(MainWindow, "_restore_settings", lambda self: None):
        window = MainWindow()
    editor_macro = MacroData(
        meta=meta, settings=MacroSettings(), raw_events=[], events=[]
    )
    window._macro = editor_macro
    window._current_file = Path(directory) / "editor.json"
    slots = list(default_quick_run_slots())
    slots[0] = QuickRunSlot(index=1, name="공통 전처리", macro_path=path)
    window._quick_run_slots = tuple(slots)
    with patch.object(window, "_start_playback") as start:
        window._run_quick_slot(1)
    assert window._macro is editor_macro
    assert window._current_file.name == "editor.json"
    started = start.call_args.kwargs["playback_macro"]
    assert [event.id for event in started.events] == ["slot-wait"]
    assert start.call_args.kwargs["source_label"] == "빠른 실행: 공통 전처리"
    window.close()
"""
    )
    assert result.returncode == 0, result.stderr
