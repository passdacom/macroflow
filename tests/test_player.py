"""player.py 재생 엔진 테스트."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from macroflow import player
from macroflow.player import (
    PlaybackError,
    _color_matches,
    _event_timing_compensation_ns,
    _execute_event,
    _hex_to_rgb,
    _PlayState,
)
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
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

    def test_pause_preserves_remaining_scheduled_delay_without_catch_up(self) -> None:
        executed_at: list[float] = []
        first_done = threading.Event()
        second_done = threading.Event()
        events: list[AnyEvent] = [
            MouseMoveEvent(
                id="first", type="mouse_move", timestamp_ns=0, x_ratio=0.1, y_ratio=0.1
            ),
            MouseMoveEvent(
                id="second",
                type="mouse_move",
                timestamp_ns=250_000_000,
                x_ratio=0.2,
                y_ratio=0.2,
            ),
        ]

        def _on_event(_idx: int, event: AnyEvent) -> None:
            executed_at.append(time.perf_counter())
            if event.id == "first":
                first_done.set()
            else:
                second_done.set()

        player.play(_make_macro(events), on_event=_on_event)
        assert first_done.wait(timeout=1.0)
        time.sleep(0.04)
        assert player.pause()
        time.sleep(0.30)
        resumed_at = time.perf_counter()
        assert player.resume()
        assert second_done.wait(timeout=1.0)

        remaining_ms = (executed_at[1] - resumed_at) * 1000
        assert 140 <= remaining_ms <= 260

    def test_pause_freezes_wait_event_active_duration(self) -> None:
        started = threading.Event()
        completed_at: list[float] = []
        event = WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=220)

        player.play(
            _make_macro([event]),
            on_event_start=lambda _idx, _event: started.set(),
            on_complete=lambda: completed_at.append(time.perf_counter()),
        )
        assert started.wait(timeout=1.0)
        time.sleep(0.04)
        assert player.pause()
        time.sleep(0.25)
        resumed_at = time.perf_counter()
        assert player.resume()
        deadline = time.monotonic() + 1.0
        while not completed_at and time.monotonic() < deadline:
            time.sleep(0.005)

        assert completed_at
        remaining_ms = (completed_at[0] - resumed_at) * 1000
        assert 110 <= remaining_ms <= 240

    def test_stop_terminates_promptly_while_paused(self) -> None:
        started = threading.Event()
        player.play(
            _make_macro([WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=5000)]),
            on_event_start=lambda _idx, _event: started.set(),
        )
        assert started.wait(timeout=1.0)
        assert player.pause()

        stop_started = time.perf_counter()
        player.stop()

        assert time.perf_counter() - stop_started < 0.5
        assert not player.is_playing()
        assert not player.is_paused()

    def test_pause_defers_until_interrupted_key_gesture_is_complete(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sent: list[tuple[int, bool]] = []
        first_done = threading.Event()
        completed = threading.Event()
        monkeypatch.setattr(player, "send_key", lambda vk, is_down: sent.append((vk, is_down)))
        events: list[AnyEvent] = [
            KeyEvent(id="ctrl-down", type="key_down", timestamp_ns=0, key="ctrl", vk_code=0x11),
            KeyEvent(id="c-down", type="key_down", timestamp_ns=40_000_000, key="c", vk_code=0x43),
            KeyEvent(id="c-up", type="key_up", timestamp_ns=50_000_000, key="c", vk_code=0x43),
            KeyEvent(id="ctrl-up", type="key_up", timestamp_ns=60_000_000, key="ctrl", vk_code=0x11),
            KeyEvent(id="a-down", type="key_down", timestamp_ns=200_000_000, key="a", vk_code=0x41),
            KeyEvent(id="a-up", type="key_up", timestamp_ns=210_000_000, key="a", vk_code=0x41),
        ]

        player.play(
            _make_macro(events),
            on_event=lambda idx, _event: first_done.set() if idx == 0 else None,
            on_complete=completed.set,
        )
        assert first_done.wait(timeout=1.0)
        assert player.pause()
        deadline = time.monotonic() + 1.0
        while len(sent) < 4 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert sent == [(0x11, True), (0x43, True), (0x43, False), (0x11, False)]
        time.sleep(0.05)
        assert len(sent) == 4
        assert player.resume()
        assert completed.wait(timeout=1.0)

        assert sent == [
            (0x11, True),
            (0x43, True),
            (0x43, False),
            (0x11, False),
            (0x41, True),
            (0x41, False),
        ]

    def test_start_pause_gate_blocks_first_event_until_resume(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sent = threading.Event()
        gate = threading.Event()
        gate.set()
        monkeypatch.setattr(player, "send_key", lambda _vk, is_down: sent.set())

        player.play(
            _make_macro(
                [KeyEvent(id="key", type="key_down", timestamp_ns=0, key="a", vk_code=0x41)]
            ),
            start_pause_requested=gate.is_set,
        )
        time.sleep(0.05)
        assert player.is_paused()
        assert not sent.is_set()

        gate.clear()
        assert player.resume()
        assert sent.wait(timeout=1.0)

    def test_playback_error_releases_held_key_once(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from macroflow.types import WindowTriggerEvent

        sent: list[tuple[int, bool]] = []
        errors: list[Exception] = []
        monkeypatch.setattr(player, "send_key", lambda vk, is_down: sent.append((vk, is_down)))
        monkeypatch.setattr(player, "find_window", lambda _title: None)
        player.play(
            _make_macro(
                [
                    KeyEvent(
                        id="ctrl-down", type="key_down", timestamp_ns=0, key="ctrl", vk_code=0x11
                    ),
                    WindowTriggerEvent(
                        id="error",
                        type="window_trigger",
                        timestamp_ns=1_000_000,
                        window_title_contains="never",
                        timeout_ms=1,
                        on_timeout="error",
                    ),
                    KeyEvent(
                        id="ctrl-up", type="key_up", timestamp_ns=2_000_000, key="ctrl", vk_code=0x11
                    ),
                ]
            ),
            on_error=errors.append,
        )
        deadline = time.monotonic() + 1.0
        while player.is_playing() and time.monotonic() < deadline:
            time.sleep(0.005)

        assert errors
        assert sent == [(0x11, True), (0x11, False)]

    def test_on_event_error_releases_held_key_and_reports_terminal_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sent: list[tuple[int, bool]] = []
        errors: list[Exception] = []
        monkeypatch.setattr(player, "send_key", lambda vk, is_down: sent.append((vk, is_down)))

        player.play(
            _make_macro(
                [
                    KeyEvent(id="down", type="key_down", timestamp_ns=0, key="a", vk_code=0x41),
                    KeyEvent(id="up", type="key_up", timestamp_ns=50_000_000, key="a", vk_code=0x41),
                ]
            ),
            on_event=lambda _idx, _event: (_ for _ in ()).throw(RuntimeError("ui failed")),
            on_error=errors.append,
        )
        deadline = time.monotonic() + 1.0
        while player.is_playing() and time.monotonic() < deadline:
            time.sleep(0.005)

        assert [str(error) for error in errors] == ["ui failed"]
        assert sent == [(0x41, True), (0x41, False)]

    def test_on_event_reports_event_before_blocking_execution(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """UI 하이라이트는 오래 걸리는 이벤트가 끝난 뒤가 아니라 시작할 때 갱신한다."""
        event = WaitEvent(
            id="blocking",
            type="wait",
            timestamp_ns=0,
            duration_ms=1,
        )
        execution_started = threading.Event()
        release_execution = threading.Event()
        reported: list[tuple[int, AnyEvent]] = []

        def _blocking_execute(
            _event: AnyEvent,
            _settings: MacroSettings,
            _state: _PlayState,
        ) -> None:
            execution_started.set()
            release_execution.wait(timeout=1.0)

        monkeypatch.setattr(player, "_execute_event", _blocking_execute)
        try:
            player.play(
                _make_macro([event]),
                on_event_start=lambda idx, item: reported.append((idx, item)),
            )
            assert execution_started.wait(timeout=1.0)

            assert reported == [(0, event)]
        finally:
            release_execution.set()
            player.stop()

    def test_on_event_start_error_uses_terminal_error_callback(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        event = WaitEvent(id="event", type="wait", timestamp_ns=0, duration_ms=1)
        errors: list[Exception] = []
        completed: list[bool] = []
        executed: list[str] = []

        monkeypatch.setattr(
            player,
            "_execute_event",
            lambda item, _settings, _state: executed.append(item.id),
        )
        player.play(
            _make_macro([event]),
            on_event_start=lambda _idx, _item: (_ for _ in ()).throw(RuntimeError("ui failed")),
            on_complete=lambda: completed.append(True),
            on_error=errors.append,
        )
        deadline = time.monotonic() + 1.0
        while player.is_playing() and time.monotonic() < deadline:
            time.sleep(0.005)

        assert len(errors) == 1
        assert str(errors[0]) == "ui failed"
        assert completed == []
        assert executed == []

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

        assert len(times) == 2
        gap_ms = (times[1] - times[0]) * 1000
        # delay_override_ms=80ms, 오차 ±20ms 허용
        assert 60 <= gap_ms <= 120

    def test_delay_override_is_scaled_by_playback_speed(self) -> None:
        """재생 대기 override도 녹화 타임라인과 동일하게 속도 배율을 적용한다."""
        events: list[AnyEvent] = [
            MouseMoveEvent(
                id="00000001",
                type="mouse_move",
                timestamp_ns=0,
                x_ratio=0.1,
                y_ratio=0.1,
            ),
            MouseMoveEvent(
                id="00000002",
                type="mouse_move",
                timestamp_ns=1_000_000_000,
                delay_override_ms=160,
                x_ratio=0.2,
                y_ratio=0.2,
            ),
        ]
        times: list[float] = []

        player.play(
            _make_macro(events),
            speed=2.0,
            on_event=lambda _idx, _event: times.append(time.perf_counter()),
        )
        deadline = time.monotonic() + 1.0
        while len(times) < 2 and time.monotonic() < deadline:
            time.sleep(0.005)
        player.stop()

        assert len(times) == 2
        gap_ms = (times[1] - times[0]) * 1000
        assert 55 <= gap_ms <= 120

    def test_wait_event_duration_is_scaled_by_playback_speed(self) -> None:
        """매크로 내부 고정 대기는 재생 속도에 맞춰 짧아져야 한다."""
        completed: list[float] = []
        started = time.perf_counter()
        player.play(
            _make_macro(
                [
                    WaitEvent(
                        id="00000004",
                        type="wait",
                        timestamp_ns=0,
                        duration_ms=160,
                    )
                ]
            ),
            speed=2.0,
            on_complete=lambda: completed.append(time.perf_counter()),
        )
        deadline = time.monotonic() + 1.0
        while not completed and time.monotonic() < deadline:
            time.sleep(0.005)

        assert completed
        elapsed_ms = (completed[0] - started) * 1000
        assert 55 <= elapsed_ms <= 120

    def test_wait_event_compensates_following_timeline(self) -> None:
        """명시적 고정 대기에 소비된 시간은 후속 절대 timestamp를 밀어야 한다."""
        event = WaitEvent(
            id="00000004",
            type="wait",
            timestamp_ns=0,
            duration_ms=200,
        )

        assert (
            _event_timing_compensation_ns(event, 10_000_000_000, 10_200_000_000)
            == 200_000_000
        )


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


    def test_stop_mode_waits_for_match_before_stopping(self, mock_win32: object, monkeypatch: pytest.MonkeyPatch) -> None:
        """stop 모드도 설정 시간 동안 색 변화를 기다리고, 맞으면 클릭을 진행한다."""
        event = MouseButtonEvent(
            id="ee55ff66", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#FF0000",
            color_check_enabled=True,
            color_check_on_mismatch="stop",
        )
        settings = MacroSettings(
            color_check_click_tolerance=0,
            color_check_click_timeout_ms=1000,
            color_check_click_interval_ms=1,
        )
        state = _PlayState()
        calls = 0

        def fake_get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
            nonlocal calls
            calls += 1
            if calls < 3:
                return (0, 0, 0)
            return (255, 0, 0)

        monkeypatch.setattr(player, "get_pixel_color", fake_get_pixel_color)
        monkeypatch.setattr(player.time, "sleep", lambda seconds: None)
        player.send_mouse_button = MagicMock()  # type: ignore[method-assign]

        _execute_event(event, settings, state)

        assert calls >= 3
        player.send_mouse_button.assert_called_once_with(960, 540, "left", down=True)  # type: ignore[attr-defined]

    def test_skip_mode_waits_then_skips_when_color_never_matches(self, mock_win32: object, monkeypatch: pytest.MonkeyPatch) -> None:
        """skip 모드는 설정 시간 동안 기다린 뒤에도 안 맞을 때만 클릭을 건너뛴다."""
        event = MouseButtonEvent(
            id="ff667788", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#FF0000",
            color_check_enabled=True,
            color_check_on_mismatch="skip",
        )
        settings = MacroSettings(
            color_check_click_tolerance=0,
            color_check_click_timeout_ms=1,
            color_check_click_interval_ms=1,
        )
        state = _PlayState()
        monkeypatch.setattr(player, "get_pixel_color", lambda x, y: (0, 0, 0))
        player.send_mouse_button = MagicMock()  # type: ignore[method-assign]

        _execute_event(event, settings, state)

        player.send_mouse_button.assert_not_called()  # type: ignore[attr-defined]
        assert state.color_check_skip_button == "left"

    def test_stop_mode_raises_after_timeout_when_color_never_matches(self, mock_win32: object, monkeypatch: pytest.MonkeyPatch) -> None:
        """stop 모드는 설정 시간 이후에도 색이 안 맞으면 재생을 중단한다."""
        event = MouseButtonEvent(
            id="00112233", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#FF0000",
            color_check_enabled=True,
            color_check_on_mismatch="stop",
        )
        settings = MacroSettings(
            color_check_click_tolerance=0,
            color_check_click_timeout_ms=1,
            color_check_click_interval_ms=1,
        )
        state = _PlayState()
        monkeypatch.setattr(player, "get_pixel_color", lambda x, y: (0, 0, 0))
        player.send_mouse_button = MagicMock()  # type: ignore[method-assign]

        with pytest.raises(PlaybackError):
            _execute_event(event, settings, state)

        player.send_mouse_button.assert_not_called()  # type: ignore[attr-defined]

    def test_click_color_check_nudges_cursor_after_one_second(
        self,
        mock_win32: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """색 체크 대기 1초 이후에는 hover 갱신을 위해 커서를 미세 이동 후 복귀한다."""
        settings = MacroSettings(
            color_check_click_tolerance=0,
            color_check_click_timeout_ms=1500,
            color_check_click_interval_ms=1,
        )
        times = iter([0, 0, 0, 1_100_000_000, 1_100_000_000, 1_600_000_000])
        move = MagicMock()

        monkeypatch.setattr(player.time, "perf_counter_ns", lambda: next(times))
        monkeypatch.setattr(player.time, "sleep", lambda seconds: None)
        monkeypatch.setattr(player, "_wait_active", lambda seconds: True)
        monkeypatch.setattr(player, "get_pixel_color", lambda x, y: (0, 0, 0))
        monkeypatch.setattr(player, "send_mouse_move", move)

        matched = player._wait_for_click_color_check(960, 540, (255, 0, 0), settings)

        assert matched is False
        move.assert_any_call(959, 540)
        move.assert_any_call(960, 540)

    def test_click_color_check_timeout_zero_waits_until_match(
        self,
        mock_win32: object,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """클릭 색 체크 timeout_ms=0은 색이 나올 때까지 무제한 대기한다."""
        settings = MacroSettings(
            color_check_click_tolerance=0,
            color_check_click_timeout_ms=0,
            color_check_click_interval_ms=1,
        )
        calls = 0

        def fake_get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
            nonlocal calls
            calls += 1
            if calls < 3:
                return (0, 0, 0)
            return (255, 0, 0)

        monkeypatch.setattr(player.time, "sleep", lambda seconds: None)
        monkeypatch.setattr(player, "get_pixel_color", fake_get_pixel_color)

        matched = player._wait_for_click_color_check(960, 540, (255, 0, 0), settings)

        assert matched is True
        assert calls == 3


class TestColorTriggerInfiniteWait:
    def test_timeout_zero_waits_until_match_without_raising_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """timeout_ms=0 색 트리거는 타임아웃 없이 색이 나올 때까지 대기해야 한다."""
        event = ColorTriggerEvent(
            id="dd44ee55", type="color_trigger", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, target_color="#00FF00",
            tolerance=0, timeout_ms=0, check_interval_ms=1, on_timeout="error",
        )

        calls = 0

        def fake_get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
            nonlocal calls
            calls += 1
            if calls < 3:
                return (0, 0, 0)
            return (0, 255, 0)

        monkeypatch.setattr(player, "ratio_to_pixel", lambda xr, yr: (960, 540))
        monkeypatch.setattr(player, "send_mouse_move", lambda x, y: None)
        monkeypatch.setattr(player, "get_pixel_color", fake_get_pixel_color)

        player._wait_for_color(event)

        assert calls == 3

    def test_color_trigger_nudges_cursor_after_one_second(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """독립 색 트리거 대기 중에도 1초 이후 hover 갱신용 미세 이동을 수행한다."""
        event = ColorTriggerEvent(
            id="ee55ff66", type="color_trigger", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, target_color="#00FF00",
            tolerance=0, timeout_ms=1500, check_interval_ms=1, on_timeout="skip",
        )
        times = iter([0, 0, 0, 1_100_000_000, 1_100_000_000, 1_600_000_000])
        move = MagicMock()

        monkeypatch.setattr(player, "ratio_to_pixel", lambda xr, yr: (960, 540))
        monkeypatch.setattr(player, "send_mouse_move", move)
        monkeypatch.setattr(player, "get_pixel_color", lambda x, y: (0, 0, 0))
        monkeypatch.setattr(player.time, "perf_counter_ns", lambda: next(times))
        monkeypatch.setattr(player.time, "sleep", lambda seconds: None)
        monkeypatch.setattr(player, "_wait_active", lambda seconds: True)

        player._wait_for_color(event)

        move.assert_any_call(959, 540)
        move.assert_any_call(960, 540)


def test_stale_playback_session_cannot_stop_new_worker() -> None:
    first_done = threading.Event()
    first = player.play(
        _make_macro(
            [
                WaitEvent(
                    id="first-wait",
                    type="wait",
                    timestamp_ns=0,
                    duration_ms=1,
                )
            ]
        ),
        on_complete=first_done.set,
    )
    assert first_done.wait(timeout=1.0)

    second = player.play(
        _make_macro(
            [
                WaitEvent(
                    id="second-wait",
                    type="wait",
                    timestamp_ns=0,
                    duration_ms=1_000,
                )
            ]
        )
    )
    try:
        assert player.is_playing()
        assert player.stop(first) is False
        assert player.is_playing()
    finally:
        assert player.stop(second) is True


def test_new_playback_is_rejected_until_owned_stop_cleanup_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_entered = threading.Event()
    allow_release = threading.Event()
    original_release = player._release_active_inputs

    def blocking_release() -> None:
        if threading.current_thread().name == "owned-stopper":
            release_entered.set()
            assert allow_release.wait(timeout=1.0)
            return
        original_release()

    monkeypatch.setattr(player, "_release_active_inputs", blocking_release)
    first = player.play(
        _make_macro(
            [
                WaitEvent(
                    id="handoff-wait",
                    type="wait",
                    timestamp_ns=0,
                    duration_ms=1_000,
                )
            ]
        )
    )
    stop_result: list[bool] = []
    stopper = threading.Thread(
        target=lambda: stop_result.append(player.stop(first)),
        name="owned-stopper",
    )
    stopper.start()
    assert release_entered.wait(timeout=1.0)
    deadline = time.monotonic() + 1.0
    while player.is_playing() and time.monotonic() < deadline:
        time.sleep(0.005)
    assert not player.is_playing()

    with pytest.raises(player.PlaybackError, match="중지 정리"):
        player.play(
            _make_macro(
                [
                    WaitEvent(
                        id="too-early",
                        type="wait",
                        timestamp_ns=0,
                        duration_ms=10,
                    )
                ]
            )
        )

    allow_release.set()
    stopper.join(timeout=1.0)
    assert not stopper.is_alive()
    assert stop_result == [True]

    second = player.play(
        _make_macro(
            [
                WaitEvent(
                    id="after-cleanup",
                    type="wait",
                    timestamp_ns=0,
                    duration_ms=1_000,
                )
            ]
        )
    )
    assert player.stop(second) is True
