"""Real-PyQt subprocess regressions for runtime-only UI paths."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap


def _run_offscreen(script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def test_main_window_focused_fallback_uses_configured_real_pyqt_shortcuts() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtGui import QShortcut
        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        window.show()
        app.processEvents()
        expected = {
            "F6", "F7", "F8", "F9",
            "Ctrl+Shift+T", "Ctrl+Shift+L", "Ctrl+Shift+G",
        }
        shortcuts = [item for item in window.findChildren(QShortcut) if item.isEnabled()]
        assert {item.key().toString() for item in shortcuts} >= expected
        window.hide()
        window.show()
        app.processEvents()
        active_keys = [
            item.key().toString()
            for item in window.findChildren(QShortcut)
            if item.isEnabled() and item.key().toString() in expected
        ]
        assert len(active_keys) == 7
        window.close()
        """
    )

    assert result.returncode == 0, result.stderr


def test_playing_state_takes_priority_over_current_tab_for_f7() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "playing"
        host._stop_playback = Mock()
        host._is_sequencer_tab.return_value = True
        host._is_favorites_tab.return_value = False
        MainWindow._toggle_playback(host)

        host._stop_playback.assert_called_once_with()
        host._toggle_sequencer.assert_not_called()
        """
    )

    assert result.returncode == 0, result.stderr


def test_recording_f6_stops_recording_before_capture() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "recording"
        MainWindow._handle_f6(host)

        host._editor.cancel_f6_capture.assert_called_once_with()
        host._sequencer.cancel_f6_capture.assert_called_once_with()
        host._toggle_recording.assert_called_once_with()
        host._do_f6_capture.assert_not_called()
        """
    )

    assert result.returncode == 0, result.stderr


def test_recording_hook_failure_is_shown_without_entering_recording_ui() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._macro = None
        host._state = "idle"
        host._append_recording_mode = True
        host._append_base_macro = object()

        with patch(
            "macroflow.recorder.start_recording",
            side_effect=RuntimeError("keyboard hook registration failed"),
        ), patch("macroflow.ui.main_window.QMessageBox.critical") as critical:
            MainWindow._start_recording(host)

        assert host._state == "idle"
        assert host._append_recording_mode is False
        assert host._append_base_macro is None
        host._overlay.start_recording.assert_not_called()
        host._poll_timer.start.assert_not_called()
        assert "keyboard hook registration failed" in critical.call_args.args[2]
        """
    )

    assert result.returncode == 0, result.stderr


def test_recording_start_failure_reports_quick_run_restore_failure() -> None:
    result = _run_offscreen(
        """
        from types import SimpleNamespace
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with patch.object(MainWindow, "_restore_settings", lambda self: None):
            window = MainWindow()
        runtime = Mock()
        runtime.globally_registered = True
        runtime.set_quick_run_enabled.side_effect = [
            SimpleNamespace(success=True),
            SimpleNamespace(success=False),
        ]
        window._hotkey_runtime = runtime

        with patch("macroflow.ui.main_window.sys.platform", "win32"), \
             patch("macroflow.recorder.start_recording", side_effect=RuntimeError("boom")), \
             patch("macroflow.ui.main_window.QMessageBox.warning") as warning, \
             patch("macroflow.ui.main_window.QMessageBox.critical"):
            window._start_recording()

        assert runtime.set_quick_run_enabled.call_args_list == [
            ((False,), {}),
            ((True,), {}),
        ]
        warning.assert_called_once()
        assert "복구" in warning.call_args.args[2]
        window.close()
        """
    )

    assert result.returncode == 0, result.stderr


def test_recording_stop_terminal_error_restores_quick_run_hotkeys() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "stopping"
        host._recording_stop_thread = Mock()
        host._repeat_session = None
        host._playback_pause_event = Mock()
        host._hotkey_runtime = Mock()
        host._hotkey_runtime.set_quick_run_enabled.return_value.success = True

        with patch("macroflow.recorder.is_recording", return_value=False), \
             patch("macroflow.ui.main_window.sys.platform", "win32"), \
             patch("macroflow.ui.main_window.QMessageBox.warning"):
            MainWindow._on_play_error(host, "녹화 중지 오류: terminal failure")

        host._hotkey_runtime.set_quick_run_enabled.assert_called_once_with(True)
        assert host._state == "idle"
        """
    )

    assert result.returncode == 0, result.stderr


def test_recording_stop_failure_keeps_stopping_state_and_allows_retry() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "stopping"
        host._recording_stop_thread = Mock()
        host._repeat_session = None

        with patch("macroflow.recorder.is_recording", return_value=True), \
             patch("macroflow.ui.main_window.QMessageBox.warning") as warning:
            MainWindow._on_play_error(host, "녹화 중지 오류: hook shutdown failed")

        assert host._state == "stopping"
        assert host._recording_stop_thread is None
        host._overlay.stop.assert_not_called()
        assert "hook shutdown failed" in warning.call_args.args[2]

        host._sequencer.is_running.return_value = False
        host._toggle_recording.side_effect = lambda: MainWindow._toggle_recording(host)
        MainWindow._handle_f6(host)
        host._toggle_recording.assert_called_once_with()
        host._do_stop_recording.assert_called_once_with()
        """
    )

    assert result.returncode == 0, result.stderr


def test_recording_temp_save_failure_still_delivers_captured_macro() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        macro = object()
        host._auto_save_temp.side_effect = OSError("disk full")

        with patch("macroflow.recorder.stop_recording", return_value=macro):
            MainWindow._stop_recording_worker(host)

        host._sig_recording_done.emit.assert_called_once_with(macro)
        warning = host._sig_recording_save_warning.emit.call_args.args[0]
        assert "disk full" in warning
        """
    )

    assert result.returncode == 0, result.stderr


def test_f9_quick_text_pauses_during_dialog_and_resumes_after_target_input() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QDialog
        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "recording"
        host._paused = False
        host._append_recording_mode = False
        host._quick_text_session_active = False

        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.text.return_value = "아주 긴 텍스트"

        calls = []
        with patch("macroflow.recorder.is_paused", return_value=False), \\
             patch("macroflow.recorder.pause_recording", side_effect=lambda: calls.append("pause") or True), \\
             patch("macroflow.ui.main_window._quick_text_delay_override", return_value=100), \\
             patch("macroflow.recorder.inject_text_input", side_effect=lambda text, *, delay_override_ms: calls.append(("record", text, delay_override_ms)) or True), \\
             patch("macroflow.recorder.suppress_next_key_release", side_effect=lambda keys: calls.append(("suppress", keys))), \\
             patch("macroflow.recorder.resume_recording", side_effect=lambda: calls.append("resume") or True), \\
             patch("macroflow.win32.get_foreground_window", return_value=777), \\
             patch("macroflow.win32.bring_window_to_foreground", side_effect=lambda hwnd: calls.append(("restore", hwnd)) or True), \\
             patch("macroflow.win32.is_foreground_window", return_value=True), \\
             patch("macroflow.ui.main_window._set_quick_text_clipboard", side_effect=lambda text: calls.append(("clipboard", text)) or True), \\
             patch("macroflow.win32.send_paste", side_effect=lambda: calls.append("paste") or True), \\
             patch("macroflow.ui.main_window.QuickTextDialog", return_value=dialog):
            MainWindow._capture_quick_text(host)

        assert calls == [
            "pause",
            ("restore", 777),
            ("clipboard", "아주 긴 텍스트"),
            "paste",
            ("record", "아주 긴 텍스트", 100),
            ("restore", 777),
            ("suppress", {0x11, 0xA2, 0xA3}),
            "resume",
        ]
        host._set_recording_paused_ui.assert_any_call(True)
        host._set_recording_paused_ui.assert_called_with(False)
        """
    )

    assert result.returncode == 0, result.stderr


def test_f9_text_delay_settings_persists_app_default_without_macro() -> None:
    result = _run_offscreen(
        """
        import tempfile
        from unittest.mock import Mock, patch

        from PyQt6.QtCore import QSettings
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.quick_text_settings import QUICK_TEXT_DELAY_KEY

        with tempfile.TemporaryDirectory() as directory:
            QSettings.setDefaultFormat(QSettings.Format.IniFormat)
            QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, directory)
            host = Mock()

            with patch("macroflow.ui.main_window.QInputDialog.getInt", return_value=(250, True)):
                MainWindow._show_quick_text_delay_settings(host)

            settings = QSettings("MacroFlow", "MacroFlow")
            assert int(settings.value(QUICK_TEXT_DELAY_KEY)) == 250
            host._sb_state.setText.assert_called_once_with(
                "F9 텍스트 기본 재생 대기: 250 ms"
            )
        """
    )

    assert result.returncode == 0, result.stderr


def test_f9_quick_text_preserves_existing_pause_ownership() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QDialog
        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "recording"
        host._paused = True
        host._append_recording_mode = False
        host._quick_text_session_active = False
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.text.return_value = "paused text"

        with patch("macroflow.recorder.is_paused", return_value=True), \\
             patch("macroflow.recorder.pause_recording") as pause, \\
             patch("macroflow.recorder.inject_text_input", return_value=True), \\
             patch("macroflow.recorder.resume_recording") as resume, \\
             patch("macroflow.win32.get_foreground_window", return_value=777), \\
             patch("macroflow.win32.bring_window_to_foreground", return_value=True), \\
             patch("macroflow.win32.is_foreground_window", return_value=True), \\
             patch("macroflow.ui.main_window._set_quick_text_clipboard"), \\
             patch("macroflow.win32.send_paste", return_value=True), \\
             patch("macroflow.ui.main_window.QuickTextDialog", return_value=dialog):
            MainWindow._capture_quick_text(host)

        pause.assert_not_called()
        resume.assert_not_called()
        assert host._set_recording_paused_ui.call_count == 2
        host._set_recording_paused_ui.assert_called_with(True)
        """
    )

    assert result.returncode == 0, result.stderr


def test_f9_session_blocks_f8_resume_and_nested_f9() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "recording"
        host._paused = True
        host._quick_text_session_active = True

        with patch("macroflow.recorder.resume_recording") as resume, \\
             patch("macroflow.ui.main_window.QuickTextDialog") as dialog:
            MainWindow._toggle_pause(host)
            MainWindow._capture_quick_text(host)

        resume.assert_not_called()
        dialog.assert_not_called()
        host._sb_state.setText.assert_any_call(
            "F9 텍스트 입력 중에는 일시정지를 해제할 수 없습니다"
        )
        host._sb_state.setText.assert_called_with("F9 텍스트 입력이 이미 열려 있습니다")
        """
    )

    assert result.returncode == 0, result.stderr


def test_f9_send_failure_does_not_commit_text_event() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QDialog
        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "recording"
        host._paused = False
        host._append_recording_mode = False
        host._quick_text_session_active = False
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.text.return_value = "전송 실패 문구"

        with patch("macroflow.recorder.is_paused", return_value=False), \\
             patch("macroflow.recorder.pause_recording", return_value=True), \\
             patch("macroflow.recorder.inject_text_input") as inject, \\
             patch("macroflow.recorder.resume_recording", return_value=True), \\
             patch("macroflow.win32.get_foreground_window", return_value=777), \\
             patch("macroflow.win32.bring_window_to_foreground", return_value=True), \\
             patch("macroflow.win32.is_foreground_window", return_value=True), \\
             patch("macroflow.ui.main_window._set_quick_text_clipboard"), \\
             patch("macroflow.win32.send_paste", return_value=False), \\
             patch("macroflow.ui.main_window.QuickTextDialog", return_value=dialog), \\
             patch("macroflow.ui.main_window.QMessageBox.warning") as warning:
            MainWindow._capture_quick_text(host)

        inject.assert_not_called()
        warning.assert_called_once()
        assert host._quick_text_session_active is False
        """
    )

    assert result.returncode == 0, result.stderr


def test_f9_final_focus_failure_keeps_recording_paused() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QDialog
        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._state = "recording"
        host._paused = False
        host._append_recording_mode = False
        host._quick_text_session_active = False
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.text.return_value = "focus guarded text"

        with patch("macroflow.recorder.is_paused", return_value=False), \\
             patch("macroflow.recorder.pause_recording", return_value=True), \\
             patch("macroflow.recorder.inject_text_input", return_value=True), \\
             patch("macroflow.recorder.resume_recording") as resume, \\
             patch("macroflow.win32.get_foreground_window", return_value=777), \\
             patch("macroflow.win32.bring_window_to_foreground", side_effect=[True, False]), \\
             patch("macroflow.win32.is_foreground_window", return_value=True), \\
             patch("macroflow.ui.main_window._set_quick_text_clipboard"), \\
             patch("macroflow.win32.send_paste", return_value=True), \\
             patch("macroflow.ui.main_window.QuickTextDialog", return_value=dialog), \\
             patch("macroflow.ui.main_window.QMessageBox.warning") as warning:
            MainWindow._capture_quick_text(host)

        resume.assert_not_called()
        host._set_recording_paused_ui.assert_called_with(True)
        warning.assert_called_once_with(
            host,
            "대상 창 복원 실패",
            "원래 입력 창을 다시 확인할 수 없어 녹화를 일시중지 상태로 유지합니다.",
        )
        """
    )

    assert result.returncode == 0, result.stderr


def test_quick_text_dialog_preserves_long_multiline_text_and_korean_buttons() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication, QPushButton
        from macroflow.ui.quick_text_dialog import QuickTextDialog

        app = QApplication.instance() or QApplication([])
        dialog = QuickTextDialog()
        text = ("긴 한글 문구와 줄바꿈\\n" * 5000) + "마지막"
        dialog._editor.setPlainText(text)

        assert dialog.text() == text
        labels = {button.text() for button in dialog.findChildren(QPushButton)}
        assert {"저장 (Ctrl+Enter)", "취소"} <= labels
        assert dialog.width() >= 720 and dialog.height() >= 480
        """
    )

    assert result.returncode == 0, result.stderr


def test_move_visibility_toggle_preserves_selected_action_identity() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication
        from macroflow.types import MacroData, MacroMeta, MacroSettings, MouseButtonEvent, MouseMoveEvent
        from macroflow.ui.editor import EventEditorWidget

        app = QApplication.instance() or QApplication([])
        events = [
            MouseMoveEvent(id="move", type="mouse_move", timestamp_ns=1, x_ratio=0.1, y_ratio=0.1),
            MouseButtonEvent(id="down", type="mouse_down", timestamp_ns=2, x_ratio=0.5, y_ratio=0.5, button="left"),
            MouseButtonEvent(id="up", type="mouse_up", timestamp_ns=3, x_ratio=0.5, y_ratio=0.5, button="left"),
        ]
        macro = MacroData(
            meta=MacroMeta(version="1", app_version="test", created_at="now", screen_width=1920, screen_height=1080, dpi_scale=1.0),
            settings=MacroSettings(), raw_events=list(events), events=list(events)
        )
        widget = EventEditorWidget()
        widget.load_macro(macro)
        widget._table.selectRow(0)
        widget._act_toggle_moves.setChecked(True)
        widget._toggle_moves()

        selected = widget._selected_row_indices()
        assert selected == [1]
        assert widget._rows[selected[0]].primary_event_id == "down"
        """
    )

    assert result.returncode == 0, result.stderr


def test_overlay_pause_freezes_recording_elapsed_and_preserves_playback_progress() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.overlay import OverlayWindow

        app = QApplication.instance() or QApplication([])
        overlay = OverlayWindow()
        with patch(
            "macroflow.ui.overlay.time.monotonic",
            side_effect=[10.0, 15.0, 15.0, 25.0, 28.0, 28.0],
        ):
            overlay.start_recording()
            assert overlay._recording_text(overlay._recording_elapsed()) == "REC  00:05  #0"
            overlay.set_paused(True)
            assert overlay._recording_text(overlay._recording_elapsed()) == "PAUSE · REC  00:05  #0"
            overlay.set_paused(False)
            assert overlay._recording_text(overlay._recording_elapsed()) == "REC  00:08  #0"

        overlay.start_playing(1.0, repeat_current=3, repeat_total=10)
        overlay.set_progress(0.37)
        overlay.set_paused(True)
        assert overlay._playing_text() == "PAUSE · PLAY  3/10회  37%  1.0x"
        """
    )

    assert result.returncode == 0, result.stderr


def test_sequencer_worker_callbacks_update_visible_state_on_gui_thread() -> None:
    result = _run_offscreen(
        """
        import tempfile
        import threading
        from pathlib import Path

        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            macro_path = Path(directory) / "sample.json"
            macro_path.write_text("{}", encoding="utf-8")
            widget = MacroSequencerWidget()
            widget.add_macro_file(macro_path)
            widget._active_generation = 1

            def notify():
                widget._on_node_start("macro_000", "sample.json")
                widget._on_node_done("macro_000", True, "ok")

            worker = threading.Thread(target=notify)
            worker.start()
            worker.join()
            for _ in range(10):
                app.processEvents()

            assert widget._items[0].status == "done"
            assert widget._list.item(0).text().startswith("✅")
            log_text = widget._log.toPlainText()
            assert "실행: sample.json" in log_text
            assert "완료: ok" in log_text
        """
    )

    assert result.returncode == 0, result.stderr


def test_favorite_name_dialog_is_wide_enough_for_long_titles() -> None:
    result = _run_offscreen(
        """
        from pathlib import Path
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QDialog
        from macroflow.ui.main_window import MainWindow

        host = Mock()
        host._macro = object()
        host._current_file = Path("매우 긴 즐겨찾기 제목을 입력하기 위한 기존 매크로.json")
        host._sequence_file_mutation_blocked.side_effect = [False, False]
        host._favorites.add_favorite.return_value = True
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.textValue.return_value = "긴 즐겨찾기 제목"

        with patch("macroflow.ui.main_window.QInputDialog", return_value=dialog) as dialog_type:
            dialog_type.InputMode.TextInput = object()
            MainWindow._save_and_add_to_favorites(host)

        dialog.setMinimumWidth.assert_called_once_with(640)
        dialog.resize.assert_called_once_with(640, 160)
        dialog.setTextValue.assert_called_once_with(
            "매우 긴 즐겨찾기 제목을 입력하기 위한 기존 매크로"
        )
        host._favorites.add_favorite.assert_called_once_with(host._macro, "긴 즐겨찾기 제목")
        """
    )

    assert result.returncode == 0, result.stderr
