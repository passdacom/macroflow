"""_build_rows 상대 시간 계산 단위 테스트."""

from __future__ import annotations

import sys
import unittest.mock

# PyQt6 는 Linux CI 환경에서 libEGL 없이 import 불가 — 사전 mocking 처리
for _mod in [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = unittest.mock.MagicMock()  # type: ignore[assignment]

import pytest  # noqa: E402

from macroflow.types import (  # noqa: E402
    ColorTriggerEvent,
    MouseButtonEvent,
)
from macroflow.ui.editor import _build_rows  # noqa: E402


def _make_mouse_down(
    id_: str, ts_ns: int, x: float = 0.5, y: float = 0.5,
    delay_ms: int | None = None,
) -> MouseButtonEvent:
    return MouseButtonEvent(
        id=id_, type="mouse_down", timestamp_ns=ts_ns,
        x_ratio=x, y_ratio=y, button="left",
        delay_override_ms=delay_ms,
    )


def _make_mouse_up(id_: str, ts_ns: int, x: float = 0.5, y: float = 0.5) -> MouseButtonEvent:
    return MouseButtonEvent(
        id=id_, type="mouse_up", timestamp_ns=ts_ns,
        x_ratio=x, y_ratio=y, button="left",
    )


class TestRelativeTime:
    def test_first_row_equals_absolute(self) -> None:
        """첫 번째 행의 time_ms_rel은 절대값과 같아야 한다."""
        down = _make_mouse_down("a", 500_000_000)  # 500ms
        up = _make_mouse_up("b", 600_000_000)
        rows = _build_rows([down, up], show_moves=False)
        assert len(rows) == 1
        assert rows[0].time_ms_rel == pytest.approx(500.0, abs=1.0)

    def test_second_row_is_delta(self) -> None:
        """두 번째 행의 time_ms_rel은 이전 primary ts와의 차이."""
        events = [
            _make_mouse_down("a", 100_000_000),
            _make_mouse_up("b", 200_000_000),
            _make_mouse_down("c", 350_000_000),
            _make_mouse_up("d", 450_000_000),
        ]
        rows = _build_rows(events, show_moves=False)
        assert len(rows) == 2
        # 350ms - 100ms = 250ms
        assert rows[1].time_ms_rel == pytest.approx(250.0, abs=1.0)

    def test_delay_override_takes_precedence(self) -> None:
        """delay_override_ms가 있으면 그 값이 time_ms_rel로 사용되어야 한다."""
        events = [
            _make_mouse_down("a", 100_000_000),
            _make_mouse_up("b", 200_000_000),
            _make_mouse_down("c", 999_000_000, delay_ms=500),  # override=500
            _make_mouse_up("d", 1_100_000_000),
        ]
        rows = _build_rows(events, show_moves=False)
        assert rows[1].time_ms_rel == pytest.approx(500.0, abs=1.0)


class TestColorDisplayRows:
    def test_click_with_recorded_color_exposes_color_hex_for_swatch(self) -> None:
        """클릭 행은 내용 텍스트 옆 색상 박스를 그릴 수 있도록 색상 hex를 보존해야 한다."""
        down = MouseButtonEvent(
            id="a", type="mouse_down", timestamp_ns=100_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#123ABC",
        )
        up = _make_mouse_up("b", 120_000_000)

        rows = _build_rows([down, up], show_moves=False)

        assert rows[0].detail == "(50.0%, 50.0%) [#123ABC]"
        assert rows[0].color_hex == "#123ABC"

    def test_color_trigger_exposes_target_color_for_swatch(self) -> None:
        """색 트리거 행도 target_color를 색상 박스로 표시할 수 있어야 한다."""
        event = ColorTriggerEvent(
            id="c", type="color_trigger", timestamp_ns=200_000_000,
            x_ratio=0.25, y_ratio=0.75, target_color="#FFFFFF",
        )

        rows = _build_rows([event], show_moves=False)

        assert rows[0].detail == "(25.0%, 75.0%) #FFFFFF"
        assert rows[0].color_hex == "#FFFFFF"


def test_context_menu_offers_direct_color_check_mismatch_choices() -> None:
    """색 체크 불일치 동작은 순환 액션 하나가 아니라 3개 모드를 한 번에 선택할 수 있어야 한다."""
    from pathlib import Path

    source = Path("src/macroflow/ui/editor.py").read_text(encoding="utf-8")

    assert "불일치 시 동작(&M)" in source
    assert "스킵(&S)" in source
    assert "중지(&T)" in source
    assert "대기(&W)" in source
    assert "_set_color_check_mode(row_idx, mode)" in source
