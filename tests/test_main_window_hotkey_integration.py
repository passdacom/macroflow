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
            active_runtime_vks = frozenset({0x79, 0x7A, 0x7B, 0x7C})
            def __init__(self, result):
                self.result = result
            def apply(self, candidate):
                self.candidate = candidate
                return self.result
            def shutdown(self):
                pass

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        candidate = DEFAULT_HOTKEY_CONFIG.with_bindings({
            "runtime.record_or_capture": "F10",
            "runtime.play_or_color_capture": "F11",
            "runtime.pause_or_resume": "F12",
            "recording.quick_text": "F13",
        })

        success = FakeRuntime(RegistrationResult(success=True))
        window._hotkey_runtime = success
        with (
            patch("macroflow.ui.main_window.save_hotkey_config") as save,
            patch("macroflow.recorder.configure_filtered_hotkey_vk_codes") as configure,
        ):
            applied = window._apply_hotkey_config(candidate)
        assert applied.success
        assert window._hotkey_config == candidate
        save.assert_called_once()
        configure.assert_called_once_with(success.active_runtime_vks)
        assert "F10" in window._act_record.text()

        failed_candidate = candidate.with_bindings({"runtime.record_or_capture": "F14"})
        failure = FakeRuntime(
            RegistrationResult(
                success=False,
                failed_action_id="runtime.record_or_capture",
                failed_key="F14",
                rollback_succeeded=True,
            )
        )
        window._hotkey_runtime = failure
        with (
            patch("macroflow.ui.main_window.save_hotkey_config") as save,
            patch("macroflow.recorder.configure_filtered_hotkey_vk_codes") as configure,
        ):
            rejected = window._apply_hotkey_config(failed_candidate)
        assert not rejected.success
        assert window._hotkey_config == candidate
        save.assert_not_called()
        configure.assert_not_called()
        window.close()
        """
    )
    assert result.returncode == 0, result.stderr
