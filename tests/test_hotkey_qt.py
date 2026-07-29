"""Real-Qt tests for configurable shortcut adapters and dialog validation."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap


def _run_offscreen(script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_qt_focused_bindings_replace_without_active_stale_shortcuts() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication, QWidget

        from macroflow.ui.hotkey_shortcuts import QtFocusedHotkeyBindings

        app = QApplication.instance() or QApplication([])
        parent = QWidget()
        calls = []
        bindings = QtFocusedHotkeyBindings(parent)
        bindings.replace({"one": "F6", "two": "Ctrl+Shift+T"}, calls.append)
        assert bindings.count == 2
        bindings._shortcuts[0].activated.emit()
        assert calls == ["one"]

        old = list(bindings._shortcuts)
        bindings.replace({"three": "F10"}, calls.append)
        assert bindings.count == 1
        assert all(not shortcut.isEnabled() for shortcut in old)
        bindings._shortcuts[0].activated.emit()
        assert calls == ["one", "three"]
        bindings.clear()
        assert bindings.count == 0
        parent.close()
        """
    )
    assert result.returncode == 0, result.stderr


def test_hotkey_dialog_rejects_duplicate_candidate_and_restores_defaults() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtGui import QKeySequence
        from PyQt6.QtWidgets import QApplication, QDialog

        from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
        from macroflow.ui.hotkey_settings_dialog import HotkeySettingsDialog

        app = QApplication.instance() or QApplication([])
        candidate = DEFAULT_HOTKEY_CONFIG.with_bindings({"runtime.record_or_capture": "F10"})
        dialog = HotkeySettingsDialog(candidate)
        dialog._edits["runtime.play_or_color_capture"].setKeySequence(QKeySequence("F10"))
        with patch("macroflow.ui.hotkey_settings_dialog.QMessageBox.warning") as warning:
            dialog.accept()
        assert dialog.result() != QDialog.DialogCode.Accepted
        warning.assert_called_once()
        assert "중복" in warning.call_args.args[2]

        dialog._restore_defaults()
        assert dialog.candidate_config() == DEFAULT_HOTKEY_CONFIG
        dialog.close()
        """
    )
    assert result.returncode == 0, result.stderr
