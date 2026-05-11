"""이벤트 에디터 표시 row 순수 로직 회귀 테스트."""

from __future__ import annotations

import sys
import unittest.mock

import pytest

# PyQt6 는 Linux CI 환경에서 libEGL 없이 import 불가 — 사전 mocking 처리
for _mod in [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = unittest.mock.MagicMock()  # type: ignore[assignment]

from macroflow.types import ColorTriggerEvent, MouseButtonEvent, MouseMoveEvent  # noqa: E402
from macroflow.ui.editor_rows import _build_rows  # noqa: E402


def _mouse_down(
    id_: str,
    ts_ns: int,
    *,
    button: str = "left",
    recorded_color: str | None = None,
    color_check_enabled: bool = False,
    color_check_on_mismatch: str = "skip",
) -> MouseButtonEvent:
    return MouseButtonEvent(
        id=id_,
        type="mouse_down",
        timestamp_ns=ts_ns,
        x_ratio=0.25,
        y_ratio=0.75,
        button=button,
        recorded_color=recorded_color,
        color_check_enabled=color_check_enabled,
        color_check_on_mismatch=color_check_on_mismatch,  # type: ignore[arg-type]
    )


def _mouse_up(id_: str, ts_ns: int, *, button: str = "left") -> MouseButtonEvent:
    return MouseButtonEvent(
        id=id_,
        type="mouse_up",
        timestamp_ns=ts_ns,
        x_ratio=0.25,
        y_ratio=0.75,
        button=button,
    )


@pytest.mark.parametrize(
    ("button", "mismatch", "expected_kind", "expected_label"),
    [
        ("left", "skip", "color_check_click", "클릭(왼쪽) 🎨"),
        ("left", "stop", "color_check_click_stop", "클릭(왼쪽) 🛑"),
        ("left", "wait", "color_check_click_wait", "클릭(왼쪽) ⏳"),
        ("right", "skip", "color_check_right_click", "클릭(오른쪽) 🎨"),
        ("right", "stop", "color_check_right_click_stop", "클릭(오른쪽) 🛑"),
        ("right", "wait", "color_check_right_click_wait", "클릭(오른쪽) ⏳"),
    ],
)
def test_color_check_click_modes_are_displayed_without_changing_semantics(
    button: str,
    mismatch: str,
    expected_kind: str,
    expected_label: str,
) -> None:
    """색 체크 클릭의 skip/stop/wait 모드는 row kind/label/detail/color_hex에 고정된다."""
    down = _mouse_down(
        "down",
        100_000_000,
        button=button,
        recorded_color="#A1B2C3",
        color_check_enabled=True,
        color_check_on_mismatch=mismatch,
    )
    up = _mouse_up("up", 120_000_000, button=button)

    rows = _build_rows([down, up], show_moves=False)

    assert len(rows) == 1
    assert rows[0].kind == expected_kind
    assert rows[0].label == expected_label
    expected_detail = {
        "skip": "(25.0%, 75.0%) 🎨#A1B2C3",
        "stop": "(25.0%, 75.0%) 🛑#A1B2C3",
        "wait": "(25.0%, 75.0%) ⏳#A1B2C3",
    }[mismatch]
    assert rows[0].detail == expected_detail
    assert rows[0].color_check_enabled is True
    assert rows[0].color_check_on_mismatch == mismatch
    assert rows[0].color_hex == "#A1B2C3"


def test_recorded_color_without_color_check_remains_passive_swatch_metadata() -> None:
    """색 체크가 꺼진 클릭의 recorded_color는 수동 swatch 메타데이터로만 보존된다."""
    rows = _build_rows(
        [
            _mouse_down("down", 100_000_000, recorded_color="#123ABC"),
            _mouse_up("up", 120_000_000),
        ],
        show_moves=False,
    )

    assert rows[0].kind == "click"
    assert rows[0].label == "클릭(왼쪽)"
    assert rows[0].detail == "(25.0%, 75.0%) [#123ABC]"
    assert rows[0].color_check_enabled is False
    assert rows[0].color_hex == "#123ABC"


def test_color_trigger_row_preserves_target_color_and_infinite_timeout_metadata() -> None:
    """색 트리거 row는 target_color 표시와 timeout_ms=0 무제한 대기 의미를 보존한다."""
    event = ColorTriggerEvent(
        id="trigger",
        type="color_trigger",
        timestamp_ns=200_000_000,
        x_ratio=0.25,
        y_ratio=0.75,
        target_color="#FFFFFF",
        timeout_ms=0,
    )

    rows = _build_rows([event], show_moves=False)

    assert rows[0].kind == "color_trigger"
    assert rows[0].label == "색 트리거"
    assert rows[0].detail == "(25.0%, 75.0%) #FFFFFF"
    assert rows[0].color_hex == "#FFFFFF"
    assert event.timeout_ms == 0


def test_hidden_mouse_moves_do_not_change_relative_time_anchor() -> None:
    """숨겨진 mouse_move는 row 목록에서 빠지지만 다음 row의 상대시간 기준을 흐리면 안 된다."""
    events = [
        _mouse_down("a", 100_000_000),
        _mouse_up("b", 120_000_000),
        MouseMoveEvent(id="move", type="mouse_move", timestamp_ns=250_000_000, x_ratio=0.1, y_ratio=0.1),
        _mouse_down("c", 400_000_000),
        _mouse_up("d", 420_000_000),
    ]

    rows = _build_rows(events, show_moves=False)

    assert [row.kind for row in rows] == ["click", "click"]
    assert rows[1].time_ms_rel == pytest.approx(300.0, abs=1.0)
