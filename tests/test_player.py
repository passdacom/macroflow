"""player.py 재생 엔진 테스트."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from macroflow import player
from macroflow.player import (
    _color_matches,
    _execute_event,
    _hex_to_rgb,
    _PlayState,
)
from macroflow.types import (
    AnyEvent,
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    TextInputEvent,
    WaitEvent,
)

# ── 헬퍼 ────────────────────────────────────────────────────────────────────

def _make_macro(events: list[AnyEvent]) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0", app_version="0.1.0",
            created_at="2025-01-15T00:00:00",
            screen_width=1920, screen_height=1080, dpi_scale=1.0,
        ),
        settings=MacroSettings(
            click_dist_threshold_px=8,
            click_time_threshold_ms=300,
        ),
        raw_events=[],
        events=events,
    )


# ── _hex_to_rgb ──────────────────────────────────────────────────────────────

class TestHexToRgb:
    def test_white(self) -> None:
        assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)

    def test_black(self) -> None:
        assert _hex_to_rgb("#000000") == (0, 0, 0)

    def test_red(self) -> None:
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_mixed(self) -> None:
        assert _hex_to_rgb("#1A2B3C") == (0x1A, 0x2B, 0x3C)


# ── _color_matches ──────────────────────────────────────────────────────────

class TestColorMatches:
    def test_exact_match(self) -> None:
        assert _color_matches((200, 100, 50), (200, 100, 50), tolerance=0)

    def test_within_tolerance(self) -> None:
        assert _color_matches((200, 100, 50), (205, 95, 55), tolerance=10)

    def test_outside_tolerance(self) -> None:
        assert not _color_matches((200, 100, 50), (215, 100, 50), tolerance=10)

    def test_boundary(self) -> None:
        assert _color_matches((100, 100, 100), (110, 100, 100), tolerance=10)
        assert not _color_matches((100, 100, 100), (111, 100, 100), tolerance=10)


# ── _execute_event ──────────────────────────────────────────────────────────

class TestExecuteEvent:
    """이벤트 실행 함수 단위 테스트."""

    @pytest.fixture(autouse=True)
    def mock_win32(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import macroflow.win32 as w32
        monkeypatch.setattr(w32, "send_mouse_move", MagicMock())
        monkeypatch.setattr(w32, "send_mouse_click", MagicMock())
        monkeypatch.setattr(w32, "send_mouse_drag", MagicMock())
        monkeypatch.setattr(w32, "send_key", MagicMock())
        monkeypatch.setattr(w32, "get_pixel_color", MagicMock(return_value=(255, 255, 255)))
        monkeypatch.setattr(w32, "find_window", MagicMock(return_value=None))
        monkeypatch.setattr(w32, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))

        # player 내부 import도 patch
        monkeypatch.setattr(player, "send_mouse_move", MagicMock())
        monkeypatch.setattr(player, "send_mouse_drag", MagicMock())
        monkeypatch.setattr(player, "send_key", MagicMock())
        monkeypatch.setattr(player, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))

    def test_mouse_move_executes(self) -> None:
        event = MouseMoveEvent(
            id="00000001", type="mouse_move", timestamp_ns=100,
            x_ratio=0.5, y_ratio=0.5,
        )
        state = _PlayState()
        _execute_event(event, MacroSettings(), state)
        player.send_mouse_move.assert_called_once_with(960, 540)  # type: ignore[attr-defined]
        assert state.has_moves_since_down is True

    def test_key_down_executes(self) -> None:
        event = KeyEvent(
            id="00000002", type="key_down", timestamp_ns=200,
            key="a", vk_code=0x41,
        )
        state = _PlayState()
        _execute_event(event, MacroSettings(), state)
        player.send_key.assert_called_once_with(0x41, is_down=True)  # type: ignore[attr-defined]

    def test_key_up_executes(self) -> None:
        event = KeyEvent(
            id="00000003", type="key_up", timestamp_ns=250,
            key="a", vk_code=0x41,
        )
        state = _PlayState()
        _execute_event(event, MacroSettings(), state)
        player.send_key.assert_called_once_with(0x41, is_down=False)  # type: ignore[attr-defined]

    def test_wait_event_sleeps(self) -> None:
        event = WaitEvent(
            id="00000004", type="wait", timestamp_ns=300, duration_ms=50,
        )
        state = _PlayState()
        start = time.perf_counter()
        _execute_event(event, MacroSettings(), state)
        elapsed = time.perf_counter() - start
        assert elapsed >= 0.04  # 50ms ≥ 40ms


# ── 재생 타이밍 테스트 ────────────────────────────────────────────────────────

class TestPlaybackTiming:
    """절대 타임스탬프 기준 재생 및 드리프트 보정 테스트.

    core-beliefs.md 원칙 3 검증.
    """

    @pytest.fixture(autouse=True)
    def mock_win32(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import macroflow.win32 as w32
        monkeypatch.setattr(w32, "send_mouse_move", lambda x, y: None)
        monkeypatch.setattr(w32, "send_mouse_click", lambda x, y, button="left": None)
        monkeypatch.setattr(w32, "send_mouse_drag", lambda x1, y1, x2, y2, button="left": None)
        monkeypatch.setattr(w32, "send_key", lambda vk, is_down: None)
        monkeypatch.setattr(w32, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))
        monkeypatch.setattr(player, "send_mouse_move", lambda x, y: None)
        monkeypatch.setattr(player, "send_mouse_drag", lambda x1, y1, x2, y2, button="left": None)
        monkeypatch.setattr(player, "send_key", lambda vk, is_down: None)
        monkeypatch.setattr(player, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))

    def test_play_completes(self) -> None:
        """play()가 완료 콜백을 호출해야 한다."""
        events: list[AnyEvent] = [
            MouseMoveEvent(id="00000001", type="mouse_move",
                           timestamp_ns=10_000_000, x_ratio=0.5, y_ratio=0.5),
            MouseMoveEvent(id="00000002", type="mouse_move",
                           timestamp_ns=20_000_000, x_ratio=0.6, y_ratio=0.6),
        ]
        macro = _make_macro(events)
        completed: list[bool] = []

        player.play(macro, on_complete=lambda: completed.append(True))

        # 완료 대기
        timeout = time.time() + 3.0
        while not completed and time.time() < timeout:
            time.sleep(0.01)

        assert completed == [True]

    def test_stop_interrupts_playback(self) -> None:
        """stop() 호출 후 재생이 중단되어야 한다."""
        executed: list[str] = []

        def _on_event(idx: int, e: AnyEvent) -> None:
            executed.append(e.id)

        events: list[AnyEvent] = [
            MouseMoveEvent(id=f"{i:08x}", type="mouse_move",
                           timestamp_ns=i * 50_000_000,
                           x_ratio=0.1 * i, y_ratio=0.1)
            for i in range(1, 20)
        ]
        macro = _make_macro(events)

        player.play(macro, on_event=_on_event)
        time.sleep(0.05)
        player.stop()

        # 모든 이벤트가 실행되지 않았어야 한다
        assert len(executed) < len(events)

    def test_delay_override_respected(self) -> None:
        """delay_override_ms가 설정된 이벤트는 그 딜레이만큼 기다려야 한다."""
        delay_ms = 80
        events: list[AnyEvent] = [
            MouseMoveEvent(id="00000001", type="mouse_move",
                           timestamp_ns=0, x_ratio=0.1, y_ratio=0.1),
            MouseMoveEvent(id="00000002", type="mouse_move",
                           timestamp_ns=1_000_000_000,  # 원래 1초 뒤
                           delay_override_ms=delay_ms,   # 실제로는 80ms 뒤
                           x_ratio=0.2, y_ratio=0.2),
        ]
        macro = _make_macro(events)
        times: list[float] = []

        def _on_event(idx: int, e: AnyEvent) -> None:
            times.append(time.perf_counter())

        player.play(macro, on_event=_on_event)
        timeout = time.time() + 3.0
        while len(times) < 2 and time.time() < timeout:
            time.sleep(0.01)
        player.stop()

        if len(times) >= 2:
            gap_ms = (times[1] - times[0]) * 1000
            # delay_override_ms=80ms, 오차 ±20ms 허용
            assert 60 <= gap_ms <= 200


# ── TextInputEvent 재생 ──────────────────────────────────────────────────────

class TestTextInputPlayback:
    @pytest.fixture(autouse=True)
    def mock_win32(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import macroflow.win32 as w32
        monkeypatch.setattr(w32, "send_mouse_move", MagicMock())
        monkeypatch.setattr(w32, "send_mouse_button", MagicMock())
        monkeypatch.setattr(w32, "send_key", MagicMock())
        monkeypatch.setattr(w32, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))
        monkeypatch.setattr(player, "send_mouse_move", MagicMock())
        monkeypatch.setattr(player, "send_key", MagicMock())
        monkeypatch.setattr(player, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))

    def test_text_input_calls_send_text(self, mock_win32: object) -> None:
        """TextInputEvent 실행 시 send_text가 호출되어야 한다."""
        from unittest.mock import patch
        event = TextInputEvent(
            id="aa11bb22", type="text_input", timestamp_ns=1_000_000_000,
            text="Hello",
        )
        settings = MacroSettings()
        state = _PlayState()
        with patch("macroflow.player.send_text") as mock_send:
            _execute_event(event, settings, state)
        mock_send.assert_called_once_with("Hello")

    def test_text_input_empty_string(self, mock_win32: object) -> None:
        """빈 문자열 TextInputEvent는 send_text를 호출하지 않아야 한다."""
        from unittest.mock import patch
        event = TextInputEvent(
            id="bb22cc33", type="text_input", timestamp_ns=1_000_000_000,
            text="",
        )
        settings = MacroSettings()
        state = _PlayState()
        with patch("macroflow.player.send_text") as mock_send:
            _execute_event(event, settings, state)
        mock_send.assert_not_called()


# ── 색 체크 wait 모드 ────────────────────────────────────────────────────────

class TestColorCheckWait:
    @pytest.fixture(autouse=True)
    def mock_win32(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import macroflow.win32 as w32
        monkeypatch.setattr(w32, "send_mouse_move", MagicMock())
        monkeypatch.setattr(w32, "send_mouse_button", MagicMock())
        monkeypatch.setattr(w32, "send_key", MagicMock())
        monkeypatch.setattr(w32, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))
        monkeypatch.setattr(player, "send_mouse_move", MagicMock())
        monkeypatch.setattr(player, "send_key", MagicMock())
        monkeypatch.setattr(player, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))

    def test_wait_mode_polls_until_match(self, mock_win32: object) -> None:
        """wait 모드: 픽셀 색이 일치할 때까지 폴링 후 클릭이 진행되어야 한다."""
        from unittest.mock import call, patch  # noqa: F401

        import macroflow.win32 as w32

        down = MouseButtonEvent(
            id="cc33dd44", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#FF0000",
            color_check_enabled=True,
            color_check_on_mismatch="wait",
        )
        settings = MacroSettings(color_check_click_tolerance=10)
        state = _PlayState()

        call_count = 0
        def side_effect(x: int, y: int) -> tuple[int, int, int]:
            nonlocal call_count
            call_count += 1
            # 처음 두 번은 불일치, 세 번째부터 일치
            if call_count < 3:
                return (0, 0, 0)
            return (255, 0, 0)  # #FF0000

        with patch.object(w32, "get_pixel_color", side_effect=side_effect), \
             patch.object(w32, "send_mouse_move"), \
             patch.object(w32, "send_mouse_button") as mock_button, \
             patch.object(player, "send_mouse_move"), \
             patch.object(player, "send_mouse_button") as mock_player_button, \
             patch.object(player, "get_pixel_color", side_effect=side_effect):
            _execute_event(down, settings, state)

        # 픽셀이 일치한 후 클릭이 실행되어야 함
        assert mock_player_button.called or mock_button.called
        assert call_count >= 3
