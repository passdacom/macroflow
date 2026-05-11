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

from macroflow.types import (  # noqa: E402
    ColorTriggerEvent,
    MouseButtonEvent,
    MouseMoveEvent,
    WaitEvent,
)
from macroflow.ui.editor_rows import (  # noqa: E402
    COLOR_CHECK_CLICK_KINDS,
    DISPLAY_ROW_KINDS,
    POSITION_EDIT_KINDS,
    _build_rows,
)


def _mouse_down(
    id_: str,
    ts_ns: int,
    *,
    button: str = "left",
    recorded_color: str | None = None,
    color_check_enabled: bool = False,
    color_check_on_mismatch: str = "skip",
    remark: str = "",
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
        remark=remark,
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
    assert rows[0].kind in DISPLAY_ROW_KINDS
    assert rows[0].kind in COLOR_CHECK_CLICK_KINDS
    assert rows[0].kind in POSITION_EDIT_KINDS
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
    assert rows[0].kind in DISPLAY_ROW_KINDS
    assert rows[0].kind in COLOR_CHECK_CLICK_KINDS
    assert rows[0].kind in POSITION_EDIT_KINDS
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
    assert rows[0].kind in DISPLAY_ROW_KINDS
    assert rows[0].kind not in COLOR_CHECK_CLICK_KINDS
    assert rows[0].kind not in POSITION_EDIT_KINDS
    assert rows[0].label == "색 트리거"
    assert rows[0].detail == "(25.0%, 75.0%) #FFFFFF"
    assert rows[0].color_hex == "#FFFFFF"
    assert event.timeout_ms == 0


def test_display_row_keeps_color_detail_and_remark_separate() -> None:
    """비고가 있어도 내용/detail과 색상 swatch 메타데이터는 별도로 유지한다."""
    rows = _build_rows(
        [
            _mouse_down(
                "down",
                100_000_000,
                recorded_color="#123ABC",
                remark="확인 버튼",
            ),
            _mouse_up("up", 120_000_000),
        ],
        show_moves=False,
    )

    assert rows[0].detail == "(25.0%, 75.0%) [#123ABC]"
    assert rows[0].color_hex == "#123ABC"
    assert rows[0].remark == "확인 버튼"


def test_grouped_row_uses_primary_event_remark() -> None:
    """그룹 행 비고는 primary event(mouse_down/key_down 등)의 remark를 표시한다."""
    rows = _build_rows(
        [
            _mouse_down("down", 100_000_000, remark="primary remark"),
            _mouse_up("up", 120_000_000),
        ],
        show_moves=False,
    )

    assert rows[0].primary_idx == 0
    assert rows[0].remark == "primary remark"


def test_position_edit_policy_covers_drag_orphan_and_visible_moves_only() -> None:
    """위치 편집 대상 kind 정책은 드래그/고아 클릭/표시된 이동을 포함하고 대기 행은 제외한다."""
    drag_events = [
        _mouse_down("drag-down", 100_000_000),
        MouseMoveEvent(id="m1", type="mouse_move", timestamp_ns=110_000_000, x_ratio=0.1, y_ratio=0.1),
        MouseMoveEvent(id="m2", type="mouse_move", timestamp_ns=120_000_000, x_ratio=0.2, y_ratio=0.2),
        MouseMoveEvent(id="m3", type="mouse_move", timestamp_ns=130_000_000, x_ratio=0.3, y_ratio=0.3),
        MouseMoveEvent(id="m4", type="mouse_move", timestamp_ns=140_000_000, x_ratio=0.4, y_ratio=0.4),
        _mouse_up("drag-up", 150_000_000),
    ]
    orphan_events = [_mouse_down("orphan", 200_000_000)]
    move_events = [MouseMoveEvent(id="move", type="mouse_move", timestamp_ns=300_000_000, x_ratio=0.5, y_ratio=0.5)]
    wait_events = [WaitEvent(id="wait", type="wait", timestamp_ns=400_000_000, duration_ms=500)]

    drag_row = _build_rows(drag_events, show_moves=False)[0]
    orphan_row = _build_rows(orphan_events, show_moves=False)[0]
    move_row = _build_rows(move_events, show_moves=True)[0]
    wait_row = _build_rows(wait_events, show_moves=False)[0]

    assert drag_row.kind == "drag"
    assert orphan_row.kind == "orphan"
    assert move_row.kind == "mouse_move"
    assert wait_row.kind == "wait"
    assert {drag_row.kind, orphan_row.kind, move_row.kind} <= set(POSITION_EDIT_KINDS)
    assert wait_row.kind not in POSITION_EDIT_KINDS
    assert all(row.kind in DISPLAY_ROW_KINDS for row in [drag_row, orphan_row, move_row, wait_row])


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
