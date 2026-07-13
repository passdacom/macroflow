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
            def _toggle_recording(self):
                pass

            def _toggle_playback(self):
                pass

        host = ShortcutHost()
        MainWindow._register_shortcut_fallback(host)
        assert len(host.findChildren(QShortcut)) == 2
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
