"""Real-Qt contracts for contextual MacroFlow toolbar layout and document routing."""

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


def test_contextual_two_row_toolbars_fit_supported_minimum_width() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication, QToolBar

        from macroflow.ui.main_window import MainWindow

        MainWindow._restore_settings = lambda self: None
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window.resize(860, 520)
        window.show()
        app.processEvents()

        def toolbar(owner, object_name):
            result = owner.findChild(QToolBar, object_name)
            assert result is not None, object_name
            return result

        def has_visible_overflow(item):
            extension = next(
                (child for child in item.children() if child.objectName() == "qt_toolbar_ext_button"),
                None,
            )
            return bool(extension and extension.isVisible())

        editor_edit = toolbar(window._editor, "editor-edit-toolbar")
        editor_add = toolbar(window._editor, "editor-add-toolbar")
        sequence_add = toolbar(window._sequencer, "sequencer-add-toolbar")
        sequence_manage = toolbar(window._sequencer, "sequencer-manage-toolbar")
        file_toolbar = toolbar(window, "editor-file-toolbar")

        assert [action.text() for action in editor_add.actions()] == [
            "📝 텍스트 입력 추가", "🖱 클릭 추가", "🎨 색 체크 삽입"
        ]
        assert [action.text() for action in sequence_add.actions()] == [
            "➕ 매크로", "📝 문구", "🖱 클릭", "🎨 색상 대기", "⏱ 대기"
        ]

        window._tabs.setCurrentWidget(window._editor)
        app.processEvents()
        assert file_toolbar.isVisible()
        assert not has_visible_overflow(editor_edit)
        assert not has_visible_overflow(editor_add)

        window._tabs.setCurrentWidget(window._sequencer)
        app.processEvents()
        assert not file_toolbar.isVisible()
        assert not has_visible_overflow(sequence_add)
        assert not has_visible_overflow(sequence_manage)

        window._tabs.setCurrentWidget(window._favorites)
        app.processEvents()
        assert not file_toolbar.isVisible()
        window.close()
        """
    )

    assert result.returncode == 0, result.stderr


def test_ctrl_s_routes_to_active_document_surface_only() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication

        from macroflow.types import MacroData, MacroMeta, MacroSettings
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.sequencer import MacroSequencerWidget

        calls = []
        MainWindow._restore_settings = lambda self: None
        MacroSequencerWidget.save_flow = lambda self: calls.append("sequence")
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window._macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="test", created_at="2026-07-28T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(), raw_events=[], events=[],
        )
        window._editor.load_macro(window._macro)
        window._save_file_as = lambda: calls.append("macro")
        window.show()
        app.processEvents()

        window._tabs.setCurrentWidget(window._editor)
        window._menu_save.setEnabled(True)
        app.processEvents()
        QTest.keyClick(window._editor, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        assert calls == ["macro"]

        window._tabs.setCurrentWidget(window._sequencer)
        window._menu_save.setEnabled(True)
        app.processEvents()
        QTest.keyClick(window._sequencer, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        assert calls == ["macro", "sequence"]

        window._tabs.setCurrentWidget(window._favorites)
        app.processEvents()
        QTest.keyClick(window._favorites, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        assert calls == ["macro", "sequence"]
        window.close()
        """
    )

    assert result.returncode == 0, result.stderr
