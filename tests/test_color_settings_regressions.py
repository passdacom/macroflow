"""색 체크 timeout 세분화/지속성 회귀 테스트."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from macroflow.types import MacroSettings, MouseButtonEvent


def test_click_color_check_has_independent_timeout_defaults_per_action() -> None:
    """대기/무시/중지 동작은 각자 독립 timeout 기본값을 가져야 한다."""
    settings = MacroSettings()

    assert settings.color_check_click_wait_timeout_ms == 10000
    assert settings.color_check_click_skip_timeout_ms == 10000
    assert settings.color_check_click_stop_timeout_ms == 10000


def test_player_selects_timeout_by_color_check_action() -> None:
    """클릭 색 체크 runtime은 이벤트의 mismatch action별 timeout을 선택해야 한다."""
    from macroflow.player import _color_check_timeout_ms_for_action

    settings = MacroSettings(
        color_check_click_wait_timeout_ms=111,
        color_check_click_skip_timeout_ms=222,
        color_check_click_stop_timeout_ms=333,
    )

    assert _color_check_timeout_ms_for_action(settings, "wait") == 111
    assert _color_check_timeout_ms_for_action(settings, "skip") == 222
    assert _color_check_timeout_ms_for_action(settings, "stop") == 333


@pytest.mark.parametrize(
    "wait_ms, skip_ms, stop_ms",
    [
        (10_000, 1, 10_000),
        (1, 10_000, 10_000),
        (10_000, 10_000, 1),
    ],
)
def test_player_does_not_use_legacy_for_only_one_non_default_action(
    wait_ms: int,
    skip_ms: int,
    stop_ms: int,
) -> None:
    """legacy timeout은 per-action timeout이 모두 기본값일 때만 사용한다."""
    from macroflow.player import _color_check_timeout_ms_for_action

    settings = MacroSettings(
        color_check_click_timeout_ms=1,
        color_check_click_wait_timeout_ms=wait_ms,
        color_check_click_skip_timeout_ms=skip_ms,
        color_check_click_stop_timeout_ms=stop_ms,
    )

    assert _color_check_timeout_ms_for_action(settings, "wait") == wait_ms
    assert _color_check_timeout_ms_for_action(settings, "skip") == skip_ms
    assert _color_check_timeout_ms_for_action(settings, "stop") == stop_ms


def test_player_uses_legacy_click_color_timeout_when_action_timeouts_are_default() -> None:
    """legacy 단일 timeout만 설정한 기존 호출 경로도 기존 값으로 동작해야 한다."""
    from macroflow.player import _color_check_timeout_ms_for_action

    settings = MacroSettings(color_check_click_timeout_ms=444)

    assert _color_check_timeout_ms_for_action(settings, "wait") == 444
    assert _color_check_timeout_ms_for_action(settings, "skip") == 444
    assert _color_check_timeout_ms_for_action(settings, "stop") == 444


def test_color_check_mouse_down_wait_time_compensates_following_event_timestamps() -> None:
    """색 체크 대기 시간이 끼어도 다음 이벤트들이 과거 target으로 몰려 급가속하지 않아야 한다."""
    from macroflow.player import _event_timing_compensation_ns

    event = MouseButtonEvent(
        id="down1",
        type="mouse_down",
        timestamp_ns=1_000_000_000,
        x_ratio=0.5,
        y_ratio=0.5,
        recorded_color="#112233",
        color_check_enabled=True,
        color_check_on_mismatch="wait",
    )

    assert _event_timing_compensation_ns(event, 10_000_000_000, 12_500_000_000) == 2_500_000_000


def test_plain_mouse_down_does_not_compensate_timestamps() -> None:
    """일반 클릭에는 인위적인 timestamp 보정을 넣지 않는다."""
    from macroflow.player import _event_timing_compensation_ns

    event = MouseButtonEvent(
        id="down1",
        type="mouse_down",
        timestamp_ns=1_000_000_000,
        x_ratio=0.5,
        y_ratio=0.5,
    )

    assert _event_timing_compensation_ns(event, 10_000_000_000, 12_500_000_000) == 0


def test_main_window_persists_color_settings_in_qsettings_contract() -> None:
    """색 설정은 매크로 파일 저장 없이도 앱 설정으로 저장/복원되어야 한다."""
    source = Path("src/macroflow/ui/main_window.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    methods: dict[str, ast.FunctionDef] = {}
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "MainWindow":
            methods = {
                item.name: item
                for item in node.body
                if isinstance(item, ast.FunctionDef)
            }
            break

    save_src = ast.unparse(methods["_save_settings"])
    persist_src = ast.unparse(methods["_persist_color_settings"])
    apply_src = ast.unparse(methods["_apply_persisted_color_settings"])
    load_src = ast.unparse(methods["_load_file"])

    for key in (
        "color_check_click_wait_timeout_ms",
        "color_check_click_skip_timeout_ms",
        "color_check_click_stop_timeout_ms",
        "color_trigger_default_timeout_ms",
    ):
        assert key in save_src or "_persist_color_settings" in save_src
        assert key in persist_src
        assert key in apply_src
    assert "_apply_persisted_color_settings" in load_src


def test_overlay_start_methods_force_visible_on_top_contract() -> None:
    """일반 녹화/재생 오버레이도 hint처럼 위치 재설정+show/raise/update 경로를 타야 한다."""
    source = Path("src/macroflow/ui/overlay.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    methods: dict[str, ast.FunctionDef] = {}
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "OverlayWindow":
            methods = {
                item.name: item
                for item in node.body
                if isinstance(item, ast.FunctionDef)
            }
            break

    helper_src = ast.unparse(methods["_show_on_top"])
    assert "_position_bottom_right" in helper_src
    assert "show" in helper_src
    assert "raise_" in helper_src
    assert "update" in helper_src

    assert "_show_on_top" in ast.unparse(methods["start_recording"])
    assert "_show_on_top" in ast.unparse(methods["start_playing"])
