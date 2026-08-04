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
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_toolbar_rows_stay_fixed_and_tab_actions_align() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication, QCheckBox, QToolBar

        from macroflow.ui.main_window import MainWindow

        MainWindow._restore_settings = lambda self: None
        MainWindow._initialize_hotkeys = lambda self: None
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window.resize(1280, 720)
        window.show()
        app.processEvents()

        def toolbar(owner, object_name):
            item = owner.findChild(QToolBar, object_name)
            assert item is not None, object_name
            return item

        runtime = toolbar(window, "runtime-control-toolbar")
        playback = toolbar(window, "playback-settings-toolbar")
        range_toolbar = toolbar(window, "range-playback-toolbar")
        editor_file = toolbar(window._editor, "editor-file-toolbar")
        editor_edit = toolbar(window._editor, "editor-edit-toolbar")
        sequence_file = toolbar(window._sequencer, "sequencer-flow-toolbar")
        sequence_manage = toolbar(window._sequencer, "sequencer-manage-toolbar")
        favorites_manage = toolbar(window._favorites, "favorites-manage-toolbar")

        assert window._editor.findChild(QToolBar, "editor-history-toolbar") is None
        assert window._editor.findChild(QToolBar, "editor-export-toolbar") is None
        assert playback.geometry().y() == range_toolbar.geometry().y()
        assert runtime.geometry().y() < playback.geometry().y()

        assert [action.text() for action in editor_file.actions() if action.text()] == [
            "📂 매크로 열기", "💾 매크로 저장", "💾 다른 이름으로 저장"
        ]
        assert [action.text() for action in sequence_file.actions() if action.text()] == [
            "📂 플로우 열기", "💾 플로우 저장", "💾 플로우 다른 이름으로 저장"
        ]
        assert "🔗 매크로로 병합" in [
            action.text() for action in sequence_manage.actions() if action.text()
        ]
        assert (
            editor_file.geometry().y()
            == sequence_file.geometry().y()
            == favorites_manage.geometry().y()
            == 0
        )
        edit_actions = editor_edit.actions()
        assert not any(
            left.isSeparator() and right.isSeparator()
            for left, right in zip(edit_actions, edit_actions[1:], strict=False)
        )
        assert [action.text() for action in edit_actions if action.text()] == [
            "이동 표시", "이동 삭제", "재생 대기",
            "시퀀서에 추가", "즐겨찾기로 저장", "이전 복원",
            "↩ 취소", "↪ 재실행", "원본 복원",
        ]
        interval = window._editor.findChild(QCheckBox)
        editor_add = toolbar(window._editor, "editor-add-toolbar")
        assert interval is not None and editor_add.isAncestorOf(interval)

        for tab in (window._editor, window._sequencer, window._favorites, window._quick_run):
            window._tabs.setCurrentWidget(tab)
            app.processEvents()
            assert runtime.isVisible()
            assert playback.isVisible()
            assert range_toolbar.isVisible()
            assert playback.geometry().y() == range_toolbar.geometry().y()

        window._tabs.setCurrentWidget(window._sequencer)
        app.processEvents()
        assert window._speed_combo.isEnabled()
        assert not window._repeat_spin.isEnabled()
        assert not window._interval_spin.isEnabled()
        assert not window._range_start_spin.isEnabled()
        assert not window._range_end_spin.isEnabled()
        assert not window._act_range_play.isEnabled()

        window._tabs.setCurrentWidget(window._favorites)
        app.processEvents()
        assert not window._act_record.isEnabled()
        assert not window._act_append_record.isEnabled()
        assert not window._act_play.isEnabled()
        assert not window._act_pause.isEnabled()
        assert not window._act_stop.isEnabled()
        assert not window._speed_combo.isEnabled()
        assert not window._repeat_spin.isEnabled()
        assert not window._interval_spin.isEnabled()
        assert not window._range_start_spin.isEnabled()
        assert not window._range_end_spin.isEnabled()
        assert not window._act_range_play.isEnabled()
        window.close()
        """
    )

    assert result.returncode == 0, result.stderr


def test_toolbar_rows_fit_initial_width_without_restricting_manual_shrink() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication, QToolBar

        from macroflow.ui.main_window import MainWindow

        MainWindow._restore_settings = lambda self: None
        MainWindow._initialize_hotkeys = lambda self: None
        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        assert window.minimumWidth() == 0
        assert window.width() == 1180
        window.resize(480, 620)
        assert window.width() == 480
        window.resize(1180, 620)
        window.show()
        app.processEvents()
        assert window.minimumWidth() == 0
        assert window.minimumHeight() == 0
        window.resize(100, 100)
        app.processEvents()
        assert (window.width(), window.height()) == (100, 100)
        window.resize(1180, 620)
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
        sequence_flow = toolbar(window._sequencer, "sequencer-flow-toolbar")
        sequence_manage = toolbar(window._sequencer, "sequencer-manage-toolbar")
        file_toolbar = toolbar(window, "editor-file-toolbar")
        playback_toolbar = toolbar(window, "playback-settings-toolbar")
        range_toolbar = toolbar(window, "range-playback-toolbar")

        assert [action.text() for action in editor_add.actions() if action.text()] == [
            "📝 텍스트 입력 추가", "🖱 클릭 추가", "🎨 색 체크 삽입"
        ]
        assert [action.text() for action in sequence_add.actions()] == [
            "➕ 매크로 추가", "📝 문구 추가", "🖱 클릭 추가",
            "🎨 색상 대기 추가", "⏱ 대기 추가"
        ]

        window._tabs.setCurrentWidget(window._editor)
        app.processEvents()
        assert file_toolbar.isVisible()
        assert playback_toolbar.isVisible()
        assert range_toolbar.isVisible()
        assert not has_visible_overflow(editor_edit)
        assert not has_visible_overflow(editor_add)
        assert editor_edit.actions()[-1].text() == "원본 복원"

        window._tabs.setCurrentWidget(window._sequencer)
        app.processEvents()
        assert not file_toolbar.isVisible()
        assert not window._act_new_record_menu.isEnabled()
        assert not has_visible_overflow(sequence_add)
        assert not has_visible_overflow(sequence_flow)
        assert not has_visible_overflow(sequence_manage)
        assert range_toolbar.isVisible()

        window._tabs.setCurrentWidget(window._favorites)
        app.processEvents()
        assert not file_toolbar.isVisible()
        assert not window._act_new_record_menu.isEnabled()
        assert playback_toolbar.isVisible()
        assert range_toolbar.isVisible()
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
        MainWindow._initialize_hotkeys = lambda self: None
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


def test_toolbars_can_be_widened_to_fit_larger_accessibility_font() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import QApplication, QToolBar

        from macroflow.ui.main_window import MainWindow

        MainWindow._restore_settings = lambda self: None
        MainWindow._initialize_hotkeys = lambda self: None
        app = QApplication.instance() or QApplication([])
        app.setFont(QFont(app.font().family(), 20))
        window = MainWindow()
        assert window.minimumWidth() == 0
        window.resize(1920, 720)
        window.show()
        app.processEvents()

        def toolbar(object_name):
            item = window.findChild(QToolBar, object_name)
            assert item is not None, object_name
            return item

        def actions_fit(item):
            right_edge = item.contentsRect().right()
            for action in item.actions():
                widget = item.widgetForAction(action)
                if widget is not None:
                    assert widget.isVisible(), action.text()
                    assert widget.geometry().right() <= right_edge, action.text()

        window._tabs.setCurrentWidget(window._editor)
        app.processEvents()
        editor_edit = toolbar("editor-edit-toolbar")
        actions_fit(toolbar("playback-settings-toolbar"))
        actions_fit(toolbar("range-playback-toolbar"))
        actions_fit(toolbar("editor-file-toolbar"))
        actions_fit(editor_edit)

        window._tabs.setCurrentWidget(window._sequencer)
        app.processEvents()
        actions_fit(toolbar("playback-settings-toolbar"))
        actions_fit(toolbar("range-playback-toolbar"))
        actions_fit(toolbar("sequencer-flow-toolbar"))
        actions_fit(toolbar("sequencer-manage-toolbar"))

        window._tabs.setCurrentWidget(window._favorites)
        app.processEvents()
        assert toolbar("runtime-control-toolbar").isVisible()
        assert toolbar("playback-settings-toolbar").isVisible()
        assert toolbar("range-playback-toolbar").isVisible()
        window.close()
        """
    )
    assert result.returncode == 0, result.stderr


def test_playback_spinboxes_show_their_largest_values_without_clipping() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import QApplication, QStyle, QStyleOptionSpinBox

        from macroflow.ui.main_window import MainWindow

        MainWindow._restore_settings = lambda self: None
        MainWindow._initialize_hotkeys = lambda self: None
        app = QApplication.instance() or QApplication([])
        app.setFont(QFont(app.font().family(), 20))
        window = MainWindow()
        window.resize(1920, 720)
        window.show()

        values = (
            (window._repeat_spin, 9999),
            (window._interval_spin, 60000),
            (window._range_start_spin, 999999),
            (window._range_end_spin, 999999),
            (window._sequencer._gap_spin, 30000),
        )
        for spin, value in values:
            spin.setMaximum(value)
            spin.setValue(value)
        app.processEvents()

        for spin, _value in values:
            editor = spin.lineEdit()
            assert editor is not None
            text_width = editor.fontMetrics().horizontalAdvance(spin.text())
            assert text_width + 12 <= editor.contentsRect().width(), (
                spin.text(), text_width, editor.contentsRect().width()
            )
            option = QStyleOptionSpinBox()
            option.initFrom(spin)
            up_button = spin.style().subControlRect(
                QStyle.ComplexControl.CC_SpinBox,
                option,
                QStyle.SubControl.SC_SpinBoxUp,
                spin,
            )
            assert up_button.width() <= 16, up_button.width()
        window.close()
        """
    )
    assert result.returncode == 0, result.stderr
