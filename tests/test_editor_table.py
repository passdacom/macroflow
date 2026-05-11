"""이벤트 에디터 Qt table rendering helper 회귀 테스트."""

from __future__ import annotations

import importlib
import sys
import types

import pytest


class _AlignmentFlag:
    AlignCenter = 0x0004
    AlignLeft = 0x0001
    AlignVCenter = 0x0080


class _ItemFlag:
    ItemIsEditable = 0x0002


class _Qt:
    AlignmentFlag = _AlignmentFlag
    ItemFlag = _ItemFlag


class _QWidget:
    def __init__(self) -> None:
        self.layout = None


class _QHBoxLayout:
    def __init__(self, widget: _QWidget) -> None:
        self.widget = widget
        self.widget.layout = self
        self.contents_margins: tuple[int, int, int, int] | None = None
        self.spacing: int | None = None
        self.widgets: list[object] = []
        self.stretches: list[int] = []

    def setContentsMargins(self, left: int, top: int, right: int, bottom: int) -> None:
        self.contents_margins = (left, top, right, bottom)

    def setSpacing(self, spacing: int) -> None:
        self.spacing = spacing

    def addWidget(self, widget: object) -> None:
        self.widgets.append(widget)

    def addStretch(self, stretch: int) -> None:
        self.stretches.append(stretch)


class _QLabel:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.alignment: int | None = None
        self.fixed_size: tuple[int, int] | None = None
        self.tooltip: str | None = None
        self.stylesheet = ""

    def setAlignment(self, alignment: int) -> None:
        self.alignment = alignment

    def setFixedSize(self, width: int, height: int) -> None:
        self.fixed_size = (width, height)

    def setToolTip(self, tooltip: str | None) -> None:
        self.tooltip = tooltip

    def setStyleSheet(self, stylesheet: str) -> None:
        self.stylesheet = stylesheet


class _QTableWidgetItem:
    def __init__(self, text: str) -> None:
        self.text = text
        self._flags = 0xFFFF
        self.alignment: int | None = None

    def flags(self) -> int:
        return self._flags

    def setFlags(self, flags: int) -> None:
        self._flags = flags

    def setTextAlignment(self, alignment: int) -> None:
        self.alignment = alignment


def _install_fake_pyqt(monkeypatch: pytest.MonkeyPatch) -> None:
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.Qt = _Qt
    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QHBoxLayout = _QHBoxLayout
    qtwidgets.QLabel = _QLabel
    qtwidgets.QTableWidgetItem = _QTableWidgetItem
    qtwidgets.QWidget = _QWidget
    pyqt = types.ModuleType("PyQt6")
    pyqt.QtCore = qtcore
    pyqt.QtWidgets = qtwidgets
    monkeypatch.setitem(sys.modules, "PyQt6", pyqt)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", qtwidgets)


def _import_editor_table(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
):
    _install_fake_pyqt(monkeypatch)
    sys.modules.pop("macroflow.ui.editor_table", None)
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor_table", None))
    return importlib.import_module("macroflow.ui.editor_table")


def test_is_hex_color_accepts_only_safe_rrggbb_values(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    table = _import_editor_table(monkeypatch, request)

    assert table._is_hex_color("#A1b2C3") is True
    assert table._is_hex_color(None) is False
    assert table._is_hex_color("A1B2C3") is False
    assert table._is_hex_color("#12345") is False
    assert table._is_hex_color("#1234567") is False
    assert table._is_hex_color("#12GG34") is False


def test_cell_items_are_not_editable_by_default(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    table = _import_editor_table(monkeypatch, request)

    item = table._cell("내용")

    assert isinstance(item, _QTableWidgetItem)
    assert item.text == "내용"
    assert item.flags() & _ItemFlag.ItemIsEditable == 0


def test_color_detail_widget_adds_swatch_only_for_valid_hex_color(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    table = _import_editor_table(monkeypatch, request)

    valid_widget = table._color_detail_widget("색", "#ABCDEF")
    invalid_widget = table._color_detail_widget("색", "not-a-color")

    assert isinstance(valid_widget.layout, _QHBoxLayout)
    assert len(valid_widget.layout.widgets) == 2
    text_label, swatch = valid_widget.layout.widgets
    assert isinstance(text_label, _QLabel)
    assert text_label.text == "색"
    assert isinstance(swatch, _QLabel)
    assert swatch.fixed_size == (18, 18)
    assert swatch.tooltip == "#ABCDEF"
    assert "background-color: #ABCDEF" in swatch.stylesheet

    assert isinstance(invalid_widget.layout, _QHBoxLayout)
    assert len(invalid_widget.layout.widgets) == 1
    assert invalid_widget.layout.widgets[0].text == "색"
