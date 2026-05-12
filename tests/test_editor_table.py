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
        self.background: object | None = None
        self.foreground: object | None = None

    def flags(self) -> int:
        return self._flags

    def setFlags(self, flags: int) -> None:
        self._flags = flags

    def setTextAlignment(self, alignment: int) -> None:
        self.alignment = alignment

    def setBackground(self, background: object) -> None:
        self.background = background

    def setForeground(self, foreground: object) -> None:
        self.foreground = foreground


class _QColor:
    def __init__(self, red: int, green: int, blue: int) -> None:
        self.rgb = (red, green, blue)


class _QBrush:
    def __init__(self, color: object) -> None:
        self.color = color


def _install_fake_pyqt(monkeypatch: pytest.MonkeyPatch) -> None:
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.Qt = _Qt
    qtgui = types.ModuleType("PyQt6.QtGui")
    qtgui.QBrush = _QBrush
    qtgui.QColor = _QColor
    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QHBoxLayout = _QHBoxLayout
    qtwidgets.QLabel = _QLabel
    qtwidgets.QTableWidgetItem = _QTableWidgetItem
    qtwidgets.QWidget = _QWidget
    pyqt = types.ModuleType("PyQt6")
    pyqt.QtCore = qtcore
    pyqt.QtGui = qtgui
    pyqt.QtWidgets = qtwidgets
    monkeypatch.setitem(sys.modules, "PyQt6", pyqt)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PyQt6.QtGui", qtgui)
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


def test_table_row_items_apply_column_text_alignment_and_type_color(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    table = _import_editor_table(monkeypatch, request)
    row = types.SimpleNamespace(
        label="클릭",
        detail="(10.0%, 20.0%)",
        remark="확인",
        time_ms=1234.0,
        time_ms_rel=34.0,
        delay_str="100",
        source_file="macro.json",
        color_hex=None,
    )
    kind_color = _QColor(1, 2, 3)

    items = table._table_row_items(row, row_number=2, relative_time=True, kind_color=kind_color)

    assert [item.text for item in items] == [
        "2",
        "클릭",
        "(10.0%, 20.0%)",
        "📝 확인",
        "34",
        "100",
        "macro.json",
    ]
    assert items[table.COL_SOURCE].alignment == (_AlignmentFlag.AlignLeft | _AlignmentFlag.AlignVCenter)
    assert all(
        item.alignment == _AlignmentFlag.AlignCenter
        for col, item in enumerate(items)
        if col != table.COL_SOURCE
    )
    assert isinstance(items[table.COL_TYPE].background, _QBrush)
    assert items[table.COL_TYPE].background.color is kind_color
    assert isinstance(items[table.COL_TYPE].foreground, _QBrush)
    assert items[table.COL_TYPE].foreground.color.rgb == (255, 255, 255)


def test_table_row_items_uses_empty_content_text_when_swatch_widget_will_be_used(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    table = _import_editor_table(monkeypatch, request)
    row = types.SimpleNamespace(
        label="색 체크",
        detail="[#ABCDEF] 색깔",
        remark="",
        time_ms=1000.0,
        time_ms_rel=1000.0,
        delay_str="0",
        source_file="",
        color_hex="#ABCDEF",
    )

    items = table._table_row_items(row, row_number=1, relative_time=False, kind_color=_QColor(4, 5, 6))

    assert items[table.COL_CONTENT].text == ""
    assert items[table.COL_TIME].text == "1000"
    assert items[table.COL_REMARK].text == ""
