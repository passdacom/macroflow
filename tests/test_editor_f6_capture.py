"""Event editor F6 capture lifecycle behavior with Qt mocked out."""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock

import pytest


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


def _make_widget(editor_module):
    widget = editor_module.EventEditorWidget.__new__(editor_module.EventEditorWidget)
    widget._f6_capture_cb = None
    widget.f6_capture_started = MagicMock()
    widget.f6_capture_started.emit = MagicMock()
    widget.f6_capture_ended = MagicMock()
    widget.f6_capture_ended.emit = MagicMock()
    return widget


def test_start_f6_capture_sets_callback_updates_controls_and_minimizes_dialog(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    widget = _make_widget(editor)
    cb = MagicMock()
    dialog = MagicMock()
    button = MagicMock()
    label = MagicMock()

    widget._start_f6_capture(cb, dialog=dialog, button=button, label=label)

    assert widget._f6_capture_cb is cb
    button.setEnabled.assert_called_once_with(False)
    label.setText.assert_called_once_with("⏳ F6을 눌러 위치를 지정하세요...")
    widget.f6_capture_started.emit.assert_called_once_with()
    dialog.showMinimized.assert_called_once_with()


def test_consume_f6_capture_runs_once_and_emits_end(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    widget = _make_widget(editor)
    cb = MagicMock()
    widget._start_f6_capture(cb)

    assert widget.consume_f6_capture(0.25, 0.75, "#AABBCC") is True

    cb.assert_called_once_with(0.25, 0.75, "#AABBCC")
    assert widget._f6_capture_cb is None
    widget.f6_capture_ended.emit.assert_called_once_with()
    assert widget.consume_f6_capture(0.1, 0.2, "#000000") is False


def test_cancel_f6_capture_only_emits_when_active(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    widget = _make_widget(editor)

    widget.cancel_f6_capture()
    widget.f6_capture_ended.emit.assert_not_called()

    widget._start_f6_capture(MagicMock())
    widget.cancel_f6_capture()

    assert widget._f6_capture_cb is None
    widget.f6_capture_ended.emit.assert_called_once_with()


def test_restore_f6_capture_dialog_reenables_button_and_raises_dialog(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    editor = _import_editor(monkeypatch, request)
    widget = _make_widget(editor)
    dialog = MagicMock()
    button = MagicMock()

    widget._restore_f6_capture_dialog(dialog, button)

    dialog.showNormal.assert_called_once_with()
    dialog.raise_.assert_called_once_with()
    button.setEnabled.assert_called_once_with(True)
