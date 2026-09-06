"""Real Qt document identity, save-failure and recovery regressions."""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

_SETUP = '''
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
from macroflow import macro_file, recorder
from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
from macroflow.ui.main_window import MainWindow
app = QApplication([])
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(Path.cwd()/"settings"))
MainWindow._get_temp_dir = lambda self: Path.cwd()/"recordings"
def macro(label):
    event = WaitEvent(id=label, type="wait", timestamp_ns=0, duration_ms=100)
    return MacroData(meta=MacroMeta(version="1.0", app_version="1.9.0", created_at="", screen_width=1920, screen_height=1080, dpi_scale=1.0), settings=MacroSettings(), events=[event], raw_events=[event])
a, b = Path.cwd()/"1.json", Path.cwd()/"2.json"
macro_file.save(macro("a"), a)
macro_file.save(macro("b"), b)
'''


def _run(tmp_path: Path, body: str) -> None:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", XDG_CONFIG_HOME=str(tmp_path / "config"))
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(_SETUP) + "\n" + textwrap.dedent(body)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_startup_ignores_last_file_and_supports_empty_document(tmp_path: Path) -> None:
    _run(tmp_path, '''
        s = QSettings("MacroFlow", "MacroFlow")
        s.setValue("last_file", str(a)); s.sync()
        w = MainWindow()
        assert w._current_file is None
        assert w._macro is not None and w._macro.events == []
        assert w._editor._macro is w._macro
        assert not w._editor_is_dirty()
        w.close()
    ''')


def test_new_recording_save_as_and_restore_document_identity(tmp_path: Path) -> None:
    _run(tmp_path, '''
        w = MainWindow(); w._load_file(str(a))
        w._editor._delete_rows([0])
        assert w._editor_is_dirty()
        before = a.read_bytes()
        with patch.object(recorder, "start_recording"):
            w._start_recording()
        assert w._current_file is None
        assert w._macro.events == []
        w._on_recording_done(macro("new")); w._poll_timer.stop()
        assert w._editor_is_dirty()
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(b), "")) as dialog, patch.object(QMessageBox, "question", side_effect=AssertionError("unexpected overwrite confirmation")):
            assert w._save_file()
        assert dialog.call_count == 1
        assert w._current_file == b and not w._editor_is_dirty()
        assert a.read_bytes() == before
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard):
            w._restore_prev_macro()
        assert w._current_file == a
        assert w._macro.events == []
        assert w._editor_is_dirty()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard): w.close()
    ''')


def test_recording_failure_preserves_document_and_previous_restore(tmp_path: Path) -> None:
    _run(tmp_path, '''
        w = MainWindow(); w._load_file(str(a))
        w._prev_macro = macro("older")
        with patch.object(recorder, "start_recording", side_effect=RuntimeError("hook failed")), patch.object(QMessageBox, "critical"):
            w._start_recording()
        assert w._current_file == a and w._macro.events[0].id == "a"
        assert w._prev_macro.events[0].id == "older"
        assert not w._editor_is_dirty()
        w.close()
    ''')


def test_unsaved_open_close_cancel_and_undo_baseline(tmp_path: Path) -> None:
    _run(tmp_path, '''
        w = MainWindow(); w._load_file(str(a)); w._editor._delete_rows([0])
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel) as question:
            assert not w._load_file(str(b))
            close = QCloseEvent(); w.closeEvent(close)
        assert question.call_count == 2 and not close.isAccepted()
        assert w._current_file == a and len(w._editor._undo_stack) == 1
        w._editor._undo()
        assert not w._editor_is_dirty()
        assert w._load_file(str(b))
        w.close()
    ''')


def test_save_failures_preserve_dirty_path_bytes_and_block_close(tmp_path: Path) -> None:
    _run(tmp_path, '''
        w = MainWindow(); w._load_file(str(a)); w._editor._delete_rows([0])
        before = a.read_bytes()
        with patch.object(macro_file, "save", side_effect=PermissionError("denied")), patch.object(QMessageBox, "critical") as critical, patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Save):
            assert not w._do_save(str(b))
            close = QCloseEvent(); w.closeEvent(close)
            assert not close.isAccepted()
        assert critical.call_count == 2
        assert w._current_file == a and w._editor_is_dirty() and a.read_bytes() == before
        with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
            assert not w._save_file_as()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard): w.close()
    ''')


def test_append_retains_file_and_clean_original_restore(tmp_path: Path) -> None:
    _run(tmp_path, '''
        w = MainWindow(); w._load_file(str(a))
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes), patch.object(recorder, "start_recording"):
            w._start_append_recording()
        assert w._current_file == a
        w._on_recording_done(macro("append")); w._poll_timer.stop()
        assert w._current_file == a and w._editor_is_dirty()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard): w._restore_prev_macro()
        assert w._current_file == a and not w._editor_is_dirty()
        assert [e.id for e in w._macro.events] == ["a"]
        w.close()
    ''')


def test_document_prompt_blocks_reentrant_recording_and_save_clears_dirty(tmp_path: Path) -> None:
    _run(tmp_path, '''
        w = MainWindow(); w._load_file(str(a)); w._editor._delete_rows([0])
        def answer(*args):
            w._start_recording()
            return QMessageBox.StandardButton.Save
        with patch.object(QMessageBox, "question", side_effect=answer), patch.object(recorder, "start_recording") as start:
            assert w._load_file(str(b))
            start.assert_not_called()
        assert macro_file.load(a).events == []
        assert w._current_file == b and not w._editor_is_dirty()
        w.close()
    ''')
