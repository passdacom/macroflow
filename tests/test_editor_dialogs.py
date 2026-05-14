"""Editor dialog widget factory tests with Qt mocked out."""

from __future__ import annotations

import importlib
import sys
import types

import pytest


class _FakeAlignmentFlag:
    AlignCenter = "align-center"


class _FakeQt:
    AlignmentFlag = _FakeAlignmentFlag


class _FakeSpin:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def setRange(self, *args: object) -> None:
        self.calls.append(("setRange", args))

    def setDecimals(self, *args: object) -> None:
        self.calls.append(("setDecimals", args))

    def setSuffix(self, *args: object) -> None:
        self.calls.append(("setSuffix", args))

    def setToolTip(self, *args: object) -> None:
        self.calls.append(("setToolTip", args))

    def setValue(self, *args: object) -> None:
        self.calls.append(("setValue", args))


class _FakeLabel:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def setAlignment(self, *args: object) -> None:
        self.calls.append(("setAlignment", args))

    def setStyleSheet(self, *args: object) -> None:
        self.calls.append(("setStyleSheet", args))


class _FakeButton:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def setToolTip(self, *args: object) -> None:
        self.calls.append(("setToolTip", args))


def _install_fake_pyqt(monkeypatch: pytest.MonkeyPatch) -> None:
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.Qt = _FakeQt

    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QDoubleSpinBox = _FakeSpin
    qtwidgets.QSpinBox = _FakeSpin
    qtwidgets.QLabel = _FakeLabel
    qtwidgets.QPushButton = _FakeButton

    pyqt = types.ModuleType("PyQt6")
    monkeypatch.setitem(sys.modules, "PyQt6", pyqt)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", qtwidgets)


def _import_dialogs(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    _install_fake_pyqt(monkeypatch)
    sys.modules.pop("macroflow.ui.editor_dialogs", None)
    request.addfinalizer(lambda: sys.modules.pop("macroflow.ui.editor_dialogs", None))
    return importlib.import_module("macroflow.ui.editor_dialogs")


def test_create_percentage_spin_applies_editor_position_defaults(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    dialogs = _import_dialogs(monkeypatch, request)

    spin = dialogs.create_percentage_spin(12.5, tooltip="tooltip")

    assert spin.calls == [
        ("setRange", (-500.0, 500.0)),
        ("setDecimals", (2,)),
        ("setSuffix", (" %",)),
        ("setToolTip", ("tooltip",)),
        ("setValue", (12.5,)),
    ]


def test_create_delay_spin_applies_editor_delay_defaults(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    dialogs = _import_dialogs(monkeypatch, request)

    spin = dialogs.create_delay_spin(1000)

    assert spin.calls == [
        ("setRange", (0, 30000)),
        ("setValue", (1000,)),
        ("setSuffix", (" ms",)),
    ]


def test_create_capture_controls_applies_shared_label_and_button_settings(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    dialogs = _import_dialogs(monkeypatch, request)

    label, button = dialogs.create_capture_controls()

    assert label.text == ""
    assert label.calls == [
        ("setAlignment", ("align-center",)),
        ("setStyleSheet", ("color: #c07000; font-weight: bold;",)),
    ]
    assert button.text == "📍 화면에서 직접 지정 (F6으로 지정)"
    assert button.calls == [
        ("setToolTip", ("버튼 클릭 후 원하는 위치로 마우스를 이동하고 F6을 누르세요.",)),
    ]
