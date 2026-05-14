"""Event editor context-menu composition tests with Qt mocked out."""

from __future__ import annotations

import importlib
import sys
import types
from collections import deque
from unittest.mock import MagicMock

import pytest

from macroflow.types import (
    AnyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    TextInputEvent,
)
from macroflow.ui.editor_rows import _build_rows


class _Signal:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.emit = MagicMock()


class _FakeWidget:
    pass


class _FakeAction:
    def __init__(self, text: str) -> None:
        self.text = text
        self.triggered = MagicMock()
        self.triggered.connect = MagicMock()
        self.setCheckable = MagicMock()
        self.setChecked = MagicMock()


class _FakeMenu:
    def __init__(self, title: str | None = None) -> None:
        self.title = title
        self.actions: list[_FakeAction | str] = []
        self.submenus: list[_FakeMenu] = []

    def addAction(self, text: str) -> _FakeAction:
        action = _FakeAction(text)
        self.actions.append(action)
        return action

    def addSeparator(self) -> None:
        self.actions.append("---")

    def addMenu(self, title: str) -> _FakeMenu:
        menu = _FakeMenu(title)
        self.submenus.append(menu)
        return menu


def _install_fake_pyqt(monkeypatch: pytest.MonkeyPatch) -> None:
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.QPoint = MagicMock()
    qtcore.Qt = MagicMock()
    qtcore.pyqtSignal = _Signal

    qtgui = types.ModuleType("PyQt6.QtGui")
    for name in ["QAction", "QBrush", "QColor", "QFont", "QKeySequence", "QShortcut"]:
        setattr(qtgui, name, MagicMock())

    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    for name in [
        "QAbstractItemView",
        "QApplication",
        "QCheckBox",
        "QComboBox",
        "QDialog",
        "QDialogButtonBox",
        "QDoubleSpinBox",
        "QFormLayout",
        "QGroupBox",
        "QHBoxLayout",
        "QHeaderView",
        "QInputDialog",
        "QLabel",
        "QLineEdit",
        "QMessageBox",
        "QPushButton",
        "QRadioButton",
        "QSpinBox",
        "QTableWidget",
        "QTableWidgetItem",
        "QToolBar",
        "QVBoxLayout",
        "QWidget",
    ]:
        setattr(qtwidgets, name, MagicMock())
    qtwidgets.QMenu = _FakeMenu
    qtwidgets.QWidget = _FakeWidget

    pyqt = types.ModuleType("PyQt6")
    monkeypatch.setitem(sys.modules, "PyQt6", pyqt)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PyQt6.QtGui", qtgui)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", qtwidgets)


def _import_editor(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    _install_fake_pyqt(monkeypatch)
    for module_name in (
        "macroflow.ui.editor",
        "macroflow.ui.editor_dialogs",
        "macroflow.ui.editor_table",
    ):
        sys.modules.pop(module_name, None)
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor", None))
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor_dialogs", None))
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor_table", None))
    return importlib.import_module("macroflow.ui.editor")


def _macro_with_events(events: list[AnyEvent]) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="1.2.0",
            created_at="2026-05-11T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=[],
        events=events,
    )


def _macro_with_event(event: AnyEvent) -> MacroData:
    return _macro_with_events([event])


def _make_widget(editor_module, macro: MacroData):
    widget = editor_module.EventEditorWidget.__new__(editor_module.EventEditorWidget)
    widget._macro = macro
    widget._rows = _build_rows(macro.events, show_moves=False)
    widget._undo_stack = deque(maxlen=50)
    widget._redo_stack = []
    return widget


def _action_texts(menu: _FakeMenu) -> list[str]:
    return [action if isinstance(action, str) else action.text for action in menu.actions]


def test_single_color_checked_click_menu_includes_color_policy_submenu(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    macro = _macro_with_events(
        [
            MouseButtonEvent(
                id="click1-down",
                type="mouse_down",
                timestamp_ns=1_000_000_000,
                x_ratio=0.5,
                y_ratio=0.5,
                button="left",
                recorded_color="#112233",
                color_check_enabled=True,
                color_check_on_mismatch="stop",
            ),
            MouseButtonEvent(
                id="click1-up",
                type="mouse_up",
                timestamp_ns=1_050_000_000,
                x_ratio=0.5,
                y_ratio=0.5,
                button="left",
                recorded_color="#112233",
                color_check_enabled=True,
                color_check_on_mismatch="stop",
            ),
        ]
    )
    widget = _make_widget(editor, macro)
    menu = _FakeMenu()

    widget._add_single_row_context_actions(menu, 0)

    assert _action_texts(menu) == [
        "▶ 이 이벤트만 실행",
        "---",
        "딜레이 설정(&D)...",
        "위치 변경(&P)...",
        "🎨 색 체크 끄기(&C)",
        "💬 텍스트 입력 추가(&T)...",
        "🖱 클릭 추가(&L)...",
        "📝 비고 편집(&N)...",
        "---",
    ]
    assert [submenu.title for submenu in menu.submenus] == ["불일치 시 동작(&M)"]
    submenu = menu.submenus[0]
    assert _action_texts(submenu) == ["▶ 스킵(&S)", "⏹ 중지(&T)", "⏳ 대기(&W)"]
    checked_calls = [action.setChecked.call_args.args[0] for action in submenu.actions if not isinstance(action, str)]
    assert checked_calls == [False, True, False]


def test_text_input_menu_includes_text_edit_and_common_insert_actions(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    macro = _macro_with_event(
        TextInputEvent(
            id="text1",
            type="text_input",
            timestamp_ns=1_000_000_000,
            text="hello",
        )
    )
    widget = _make_widget(editor, macro)
    menu = _FakeMenu()

    widget._add_single_row_context_actions(menu, 0)

    assert _action_texts(menu) == [
        "▶ 이 이벤트만 실행",
        "---",
        "딜레이 설정(&D)...",
        "💬 텍스트 편집(&E)...",
        "💬 텍스트 입력 추가(&T)...",
        "🖱 클릭 추가(&L)...",
        "📝 비고 편집(&N)...",
        "---",
    ]
    actions = [action for action in menu.actions if not isinstance(action, str)]
    assert all(action.triggered.connect.called for action in actions)
