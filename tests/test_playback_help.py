"""Playback-delay help content and menu accessibility contracts."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

from macroflow.ui.help_text import PLAYBACK_DELAY_HELP


def test_playback_delay_help_explains_recorded_zero_and_hidden_move_semantics() -> None:
    assert "-1" in PLAYBACK_DELAY_HELP
    assert "녹화 타이밍" in PLAYBACK_DELAY_HELP
    assert "0ms" in PLAYBACK_DELAY_HELP
    assert "숨겨진 마우스 이동" in PLAYBACK_DELAY_HELP
    assert "스킵되지" in PLAYBACK_DELAY_HELP
    assert "이동 삭제" in PLAYBACK_DELAY_HELP
    assert "재생 속도" in PLAYBACK_DELAY_HELP
    assert "9500ms" in PLAYBACK_DELAY_HELP
    assert "마지막 이동 직후" in PLAYBACK_DELAY_HELP


def test_help_menu_exposes_playback_delay_guide() -> None:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                from PyQt6.QtWidgets import QApplication, QMessageBox
                from macroflow.ui.help_text import PLAYBACK_DELAY_HELP
                from macroflow.ui.main_window import MainWindow

                MainWindow._restore_settings = lambda self: None
                MainWindow._initialize_hotkeys = lambda self: None
                shown = []
                QMessageBox.information = lambda _parent, title, text: shown.append((title, text))
                app = QApplication.instance() or QApplication([])
                window = MainWindow()
                window._act_playback_delay_help.trigger()
                assert shown == [("재생 대기 도움말", PLAYBACK_DELAY_HELP)]
                window.close()
                """
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert result.returncode == 0, result.stderr
