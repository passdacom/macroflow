"""Event editor remark persistence behavior with Qt mocked out."""

from __future__ import annotations

import importlib
import sys
import types
from collections import deque
from unittest.mock import MagicMock

import pytest

from macroflow.types import MacroData, MacroMeta, MacroSettings, MouseButtonEvent
from macroflow.ui.editor_rows import _build_rows


class _Signal:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.emit = MagicMock()


class _FakeWidget:
    pass


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
        "QMenu",
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
    qtwidgets.QWidget = _FakeWidget

    pyqt = types.ModuleType("PyQt6")
    monkeypatch.setitem(sys.modules, "PyQt6", pyqt)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PyQt6.QtGui", qtgui)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", qtwidgets)


def _import_editor(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    _install_fake_pyqt(monkeypatch)
    for module_name in ("macroflow.ui.editor", "macroflow.ui.editor_table"):
        sys.modules.pop(module_name, None)
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor", None))
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor_table", None))
    return importlib.import_module("macroflow.ui.editor")


def _make_macro(remark: str = "") -> MacroData:
    event = MouseButtonEvent(
        id="aa11bb22",
        type="mouse_down",
        timestamp_ns=1_000_000_000,
        x_ratio=0.5,
        y_ratio=0.5,
        button="left",
        remark=remark,
    )
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
        events=[event],
    )


def _make_widget(editor_module, macro: MacroData):
    widget = editor_module.EventEditorWidget.__new__(editor_module.EventEditorWidget)
    widget._macro = macro
    widget._rows = _build_rows(macro.events, show_moves=False)
    widget._show_moves = False
    widget._undo_stack = deque(maxlen=50)
    widget._redo_stack = []
    widget._act_undo = MagicMock()
    widget._act_redo = MagicMock()
    widget._refresh = MagicMock()
    widget.macro_changed = MagicMock()
    widget.macro_changed.emit = MagicMock()
    return widget


def test_editor_columns_split_content_and_remark(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)

    assert editor._COLUMNS == ["#", "타입", "내용", "비고", "시간(ms)", "딜레이(ms)", "출처"]
    assert editor.COL_CONTENT == 2
    assert editor.COL_REMARK == 3
    assert editor.COL_DELAY == 5
    assert editor.COL_SOURCE == 6


def test_edit_remark_updates_macro_event_and_marks_edited(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    macro = _make_macro()
    widget = _make_widget(editor, macro)
    monkeypatch.setattr(editor.QInputDialog, "getText", MagicMock(return_value=("비고추가", True)))

    widget._edit_remark(0)

    assert widget._macro.events[0].remark == "비고추가"
    assert widget._macro.is_edited is True
    assert len(widget._undo_stack) == 1
    widget.macro_changed.emit.assert_called_once_with(widget._macro)


def test_remark_edit_participates_in_undo_redo(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    macro = _make_macro()
    widget = _make_widget(editor, macro)
    monkeypatch.setattr(editor.QInputDialog, "getText", MagicMock(return_value=("저장될 비고", True)))

    widget._edit_remark(0)
    assert widget._macro.events[0].remark == "저장될 비고"

    widget._undo()
    assert widget._macro.events[0].remark == ""

    widget._redo()
    assert widget._macro.events[0].remark == "저장될 비고"
