"""MainWindow integration contracts for transactional hotkey settings."""

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
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_main_window_persists_and_updates_recorder_only_after_successful_apply() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication

        from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
        from macroflow.ui.main_window import MainWindow
        from macroflow.win32.hotkeys import RegistrationResult

        class FakeRuntime:
            globally_registered = True
            degraded = False
            active_runtime_vks = frozenset({0x79, 0x7A, 0x7B, 0x7C})
            def __init__(self, result):
                self.result = result
                self.candidates = []
            def apply(self, candidate):
                self.candidate = candidate
                self.candidates.append(candidate)
                return self.result
            def shutdown(self):
                return RegistrationResult(success=True)

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        candidate = DEFAULT_HOTKEY_CONFIG.with_bindings({
            "runtime.record_or_capture": "F10",
            "runtime.play_or_color_capture": "F11",
            "runtime.pause_or_resume": "F14",
            "recording.quick_text": "F13",
            "editor.insert_text": "Alt+T",
        })

        success = FakeRuntime(RegistrationResult(success=True))
        window._hotkey_runtime = success
        with (
            patch("macroflow.ui.main_window.arm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.disarm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.save_hotkey_config") as save,
            patch("macroflow.recorder.configure_filtered_hotkey_vk_codes") as configure,
        ):
            applied = window._apply_hotkey_config(candidate)
        assert applied.success
        assert window._hotkey_config == candidate
        save.assert_called_once()
        configure.assert_called_once_with(success.active_runtime_vks)
        assert "F10" in window._act_record.text()
        assert "Alt+T" in window._editor._act_insert_text.toolTip()

        failed_candidate = candidate.with_bindings({"runtime.record_or_capture": "F15"})
        failure = FakeRuntime(
            RegistrationResult(
                success=False,
                failed_action_id="runtime.record_or_capture",
                failed_key="F15",
                rollback_succeeded=False,
            )
        )
        failure.degraded = True
        window._hotkey_runtime = failure
        with (
            patch("macroflow.ui.main_window.arm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.disarm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.save_hotkey_config") as save,
            patch("macroflow.recorder.configure_filtered_hotkey_vk_codes") as configure,
        ):
            rejected = window._apply_hotkey_config(failed_candidate)
        assert not rejected.success
        assert window._hotkey_config == candidate
        save.assert_not_called()
        configure.assert_not_called()
        window._update_toolbar()
        assert not window._act_record.isEnabled()
        assert not window._act_hotkey_settings.isEnabled()
        with patch.object(window, "_handle_f6") as record:
            window._dispatch_hotkey_action("runtime.record_or_capture")
        record.assert_not_called()
        assert "재시작" in window._sb_state.text()

        persistence = FakeRuntime(RegistrationResult(success=True))
        window._hotkey_runtime = persistence
        window._hotkey_config = candidate
        failed_candidate = candidate.with_bindings({"runtime.record_or_capture": "F15"})
        with (
            patch("macroflow.ui.main_window.arm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.disarm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.save_hotkey_config", side_effect=[False, True]),
            patch("macroflow.recorder.configure_filtered_hotkey_vk_codes") as configure,
        ):
            rejected = window._apply_hotkey_config(failed_candidate)
        assert not rejected.success
        assert rejected.failed_key == "설정 저장"
        assert rejected.rollback_succeeded
        assert persistence.candidates == [failed_candidate, candidate]
        assert window._hotkey_config == candidate
        configure.assert_not_called()

        persistence.candidates.clear()
        persistence.degraded = False
        with (
            patch("macroflow.ui.main_window.arm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.disarm_hotkey_config_recovery", return_value=True),
            patch("macroflow.ui.main_window.save_hotkey_config", side_effect=[False, False]),
            patch("macroflow.recorder.configure_filtered_hotkey_vk_codes") as configure,
        ):
            incomplete = window._apply_hotkey_config(failed_candidate)
        assert not incomplete.success
        assert not incomplete.rollback_succeeded
        assert persistence.degraded
        assert persistence.candidates == [failed_candidate, candidate]
        assert window._hotkey_config == candidate
        configure.assert_not_called()

        persistence.candidates.clear()
        persistence.degraded = False
        with patch(
            "macroflow.ui.main_window.arm_hotkey_config_recovery", return_value=False
        ):
            unprotected = window._apply_hotkey_config(failed_candidate)
        assert not unprotected.success
        assert unprotected.failed_key == "설정 복구 준비"
        assert unprotected.rollback_succeeded
        assert persistence.candidates == []

        persistence.candidates.clear()
        window._state = "recording"
        busy = window._apply_hotkey_config(failed_candidate)
        assert not busy.success
        assert busy.failed_key == "앱 사용 중"
        assert persistence.candidates == []

        window._hotkey_settings_active = True
        with patch.object(window, "_handle_f6") as record:
            window._dispatch_hotkey_action("runtime.record_or_capture")
        record.assert_not_called()
        window._hotkey_settings_active = False
        window._state = "idle"
        window.close()
        """
    )
    assert result.returncode == 0, result.stderr


def test_modal_hotkey_settings_blocks_runtime_dispatch_and_rechecks_idle_state() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QDialog

        from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
        from macroflow.ui.main_window import MainWindow
        from macroflow.win32.hotkeys import RegistrationResult

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        calls = []

        class Runtime:
            globally_registered = True
            degraded = False
            active_runtime_vks = frozenset({0x75, 0x76, 0x77, 0x78})
            def __init__(self):
                self.candidates = []
            def apply(self, candidate):
                self.candidates.append(candidate)
                return RegistrationResult(success=True)
            def shutdown(self):
                return RegistrationResult(success=True)

        class Dialog:
            def exec(self):
                window._dispatch_hotkey_action("runtime.record_or_capture")
                window._state = "recording"
                return QDialog.DialogCode.Accepted
            def candidate_config(self):
                return DEFAULT_HOTKEY_CONFIG

        runtime = Runtime()
        window._hotkey_runtime = runtime
        window._handle_f6 = lambda: calls.append("record")
        with (
            patch("macroflow.ui.main_window.HotkeySettingsDialog", return_value=Dialog()),
            patch("macroflow.ui.main_window.QMessageBox.information") as information,
        ):
            window._show_hotkey_settings()

        assert calls == []
        assert runtime.candidates == []
        information.assert_called_once()
        window._state = "idle"
        window.close()
        """
    )
    assert result.returncode == 0, result.stderr
