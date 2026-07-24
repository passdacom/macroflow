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


def test_main_window_shortcut_fallback_uses_real_pyqt_shortcut() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtGui import QShortcut
        from PyQt6.QtWidgets import QApplication, QWidget
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])

        class ShortcutHost(QWidget):
            def _handle_f6(self):
                pass

            def _toggle_recording(self):
                pass

            def _toggle_playback(self):
                pass

            def _toggle_pause(self):
                pass

        host = ShortcutHost()
        MainWindow._register_shortcut_fallback(host)
        MainWindow._register_shortcut_fallback(host)
        shortcuts = host.findChildren(QShortcut)
        assert len(shortcuts) == 3
        assert {item.key().toString() for item in shortcuts} == {"F6", "F7", "F8"}
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
