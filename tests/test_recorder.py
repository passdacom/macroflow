"""recorder.py 이벤트 캡처 로직 테스트."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

import macroflow.recorder as rec
from macroflow.recorder import _convert_raw, _process_raw, _vk_to_key
from macroflow.types import (
    ColorTriggerEvent,
    KeyEvent,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
)

# ── _convert_raw 단위 테스트 ──────────────────────────────────────────────────

class TestConvertRaw:
    """_convert_raw 함수 — raw 이벤트 → MacroEvent 변환 테스트."""

    def setup_method(self) -> None:
        """녹화 시작 타임스탬프와 화면 크기를 설정한다."""
        rec._rec_start_ns = 0
        rec._screen_w = 1920
        rec._screen_h = 1080
        rec._pause_intervals = []
        rec._pause_started_ns = None

        # pixel_to_ratio mock
        self._orig_pixel_to_ratio = None

    def test_mouse_move(self) -> None:
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.5)):
            raw: tuple[str, int, int, tuple[int, int, int]] = (
                "m", 1_000_000_000, 0x0200, (960, 540, 0)
            )
            event = _convert_raw(raw)

        assert isinstance(event, MouseMoveEvent)
        assert event.type == "mouse_move"
        assert event.timestamp_ns == 1_000_000_000
        assert event.x_ratio == pytest.approx(0.5)

    def test_mouse_left_down(self) -> None:
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.3)):
            raw = ("m", 500_000_000, 0x0201, (960, 324, 0))
            event = _convert_raw(raw)

        assert isinstance(event, MouseButtonEvent)
        assert event.type == "mouse_down"
        assert event.button == "left"

    def test_mouse_right_down(self) -> None:
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.1, 0.1)):
            raw = ("m", 100_000_000, 0x0204, (192, 108, 0))
            event = _convert_raw(raw)

        assert isinstance(event, MouseButtonEvent)
        assert event.type == "mouse_down"
        assert event.button == "right"

    def test_mouse_left_up(self) -> None:
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.5)):
            raw = ("m", 200_000_000, 0x0202, (960, 540, 0))
            event = _convert_raw(raw)

        assert isinstance(event, MouseButtonEvent)
        assert event.type == "mouse_up"
        assert event.button == "left"

    def test_key_down(self) -> None:
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.0, 0.0)):
            raw = ("k", 300_000_000, 0x0100, (0x41, 0, 0))  # 'A' key
            event = _convert_raw(raw)

        assert isinstance(event, KeyEvent)
        assert event.type == "key_down"
        assert event.key == "a"
        assert event.vk_code == 0x41

    def test_key_up(self) -> None:
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.0, 0.0)):
            raw = ("k", 350_000_000, 0x0101, (0x41, 0, 0))
            event = _convert_raw(raw)

        assert isinstance(event, KeyEvent)
        assert event.type == "key_up"

    def test_syskey_treated_as_normal(self) -> None:
        """WM_SYSKEYDOWN도 key_down으로 처리되어야 한다."""
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.0, 0.0)):
            raw = ("k", 400_000_000, 0x0104, (0x12, 0, 0))  # Alt
            event = _convert_raw(raw)

        assert isinstance(event, KeyEvent)
        assert event.type == "key_down"

    def test_unknown_wParam_returns_none(self) -> None:
        raw = ("m", 0, 0xFFFF, (0, 0, 0))
        event = _convert_raw(raw)
        assert event is None

    def test_timestamp_is_relative(self) -> None:
        """timestamp_ns는 녹화 시작(_rec_start_ns) 기준 상대값이어야 한다."""
        rec._rec_start_ns = 1_000_000_000  # 1초
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.5)):
            raw = ("m", 1_500_000_000, 0x0200, (960, 540, 0))  # 절대 1.5초
            event = _convert_raw(raw)

        assert event is not None
        assert event.timestamp_ns == 500_000_000  # 상대 0.5초

    def test_timestamp_excludes_closed_pause_interval(self) -> None:
        rec._rec_start_ns = 1_000_000_000
        rec._pause_intervals = [(1_500_000_000, 4_500_000_000)]

        before = _convert_raw(("k", 1_400_000_000, 0x0100, (0x41, 0, 0)))
        during = _convert_raw(("k", 2_000_000_000, 0x0100, (0x42, 0, 0)))
        after = _convert_raw(("k", 4_600_000_000, 0x0100, (0x43, 0, 0)))

        assert before is not None and before.timestamp_ns == 400_000_000
        assert during is None
        assert after is not None and after.timestamp_ns == 600_000_000

    def test_timestamp_excludes_multiple_pause_intervals(self) -> None:
        rec._rec_start_ns = 1_000_000_000
        rec._pause_intervals = [
            (1_500_000_000, 2_500_000_000),
            (3_000_000_000, 5_000_000_000),
        ]

        event = _convert_raw(("k", 5_250_000_000, 0x0100, (0x41, 0, 0)))

        assert event is not None
        assert event.timestamp_ns == 1_250_000_000

    def test_open_pause_discards_events_at_or_after_pause_boundary(self) -> None:
        rec._rec_start_ns = 1_000_000_000
        rec._pause_started_ns = 1_500_000_000

        before = _convert_raw(("k", 1_499_999_999, 0x0100, (0x41, 0, 0)))
        during = _convert_raw(("k", 1_500_000_000, 0x0100, (0x42, 0, 0)))

        assert before is not None
        assert during is None

    def test_f8_hotkey_is_not_recorded(self) -> None:
        assert _convert_raw(("k", 100_000_000, 0x0100, (0x77, 0, 0))) is None
        assert _convert_raw(("k", 110_000_000, 0x0101, (0x77, 0, 0))) is None

    def test_event_id_is_8hex(self) -> None:
        """생성된 이벤트 id는 8자리 hex 문자열이어야 한다."""
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.0, 0.0)):
            raw = ("m", 0, 0x0200, (0, 0, 0))
            event = _convert_raw(raw)

        assert event is not None
        assert len(event.id) == 8
        assert all(c in "0123456789abcdef" for c in event.id)

    def test_wheel_vertical_up(self) -> None:
        """WM_MOUSEWHEEL(0x020A) + 양수 delta → MouseWheelEvent vertical 위."""
        # mouseData 상위 16비트 = 0x0078 (120) → 1노치 위
        mouse_data = 120 << 16
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.5)):
            raw = ("m", 0, 0x020A, (960, 540, mouse_data))
            event = _convert_raw(raw)

        assert isinstance(event, MouseWheelEvent)
        assert event.type == "mouse_wheel"
        assert event.axis == "vertical"
        assert event.delta == 120

    def test_wheel_vertical_down(self) -> None:
        """WM_MOUSEWHEEL + 음수 delta → delta는 음수."""
        # mouseData 상위 16비트 = 0xFF88 (-120 as unsigned short)
        raw_word = (-120) & 0xFFFF
        mouse_data = raw_word << 16
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.5)):
            raw = ("m", 0, 0x020A, (960, 540, mouse_data))
            event = _convert_raw(raw)

        assert isinstance(event, MouseWheelEvent)
        assert event.delta == -120

    def test_wheel_horizontal(self) -> None:
        """WM_MOUSEHWHEEL(0x020E) → axis == 'horizontal'."""
        mouse_data = 120 << 16
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.3, 0.7)):
            raw = ("m", 0, 0x020E, (576, 756, mouse_data))
            event = _convert_raw(raw)

        assert isinstance(event, MouseWheelEvent)
        assert event.axis == "horizontal"
        assert event.delta == 120

    def test_wheel_multi_notch(self) -> None:
        """delta = 360 → 3노치 스크롤."""
        mouse_data = 360 << 16
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.5, 0.5)):
            raw = ("m", 0, 0x020A, (960, 540, mouse_data))
            event = _convert_raw(raw)

        assert isinstance(event, MouseWheelEvent)
        assert event.delta == 360


# ── _vk_to_key 테스트 ────────────────────────────────────────────────────────

class TestVkToKey:
    def test_letters(self) -> None:
        assert _vk_to_key(0x41) == "a"
        assert _vk_to_key(0x5A) == "z"

    def test_digits(self) -> None:
        assert _vk_to_key(0x30) == "0"
        assert _vk_to_key(0x39) == "9"

    def test_named_keys(self) -> None:
        assert _vk_to_key(0x0D) == "enter"
        assert _vk_to_key(0x1B) == "escape"
        assert _vk_to_key(0x75) == "f6"

    def test_unknown_key(self) -> None:
        result = _vk_to_key(0xFE)
        assert result.startswith("vk_")


def test_process_raw_closes_pre_pause_key_and_suppresses_pause_only_key() -> None:
    rec._rec_start_ns = 0
    rec._pause_intervals = [(500, 1000)]
    rec._pause_started_ns = None
    rec._recording_pressed_keys.clear()
    rec._suppressed_pause_keys.clear()

    ctrl_down = _process_raw(("k", 400, 0x0100, (0x11, 0, 0)))
    ctrl_up = _process_raw(("k", 600, 0x0101, (0x11, 0, 0)))
    assert _process_raw(("k", 700, 0x0100, (0x41, 0, 0))) is None
    assert _process_raw(("k", 1100, 0x0101, (0x41, 0, 0))) is None

    assert isinstance(ctrl_down, KeyEvent)
    assert isinstance(ctrl_up, KeyEvent)
    assert ctrl_down.type == "key_down"
    assert ctrl_up.type == "key_up"
    assert ctrl_up.timestamp_ns == 499


def test_process_raw_suppresses_auto_repeat_until_pause_key_is_released() -> None:
    rec._rec_start_ns = 0
    rec._pause_intervals = [(500, 1000)]
    rec._pause_started_ns = None
    rec._recording_pressed_keys.clear()
    rec._suppressed_pause_keys.clear()

    assert _process_raw(("k", 700, 0x0100, (0x41, 0, 0))) is None
    assert _process_raw(("k", 1100, 0x0100, (0x41, 0, 0))) is None
    assert _process_raw(("k", 1200, 0x0101, (0x41, 0, 0))) is None
    assert 0x41 not in rec._suppressed_pause_keys


# ── start/stop 통합 테스트 ────────────────────────────────────────────────────

class TestRecorderIntegration:
    """start_recording / stop_recording 흐름 테스트."""

    def test_start_stop_returns_macro_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """start/stop 후 MacroData가 반환되어야 한다."""
        import macroflow.recorder as _rec_mod
        import macroflow.win32 as w32

        monkeypatch.setattr(w32, "start_hook", lambda q: None)
        monkeypatch.setattr(w32, "stop_hook", lambda: None)
        monkeypatch.setattr(w32, "get_logical_screen_size", lambda: (1920, 1080))
        monkeypatch.setattr(w32, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))
        # recorder.py는 get_logical_screen_size를 직접 import하므로 해당 참조도 패치
        monkeypatch.setattr(_rec_mod, "get_logical_screen_size", lambda: (1920, 1080))

        rec.start_recording()
        assert rec.is_recording()

        macro = rec.stop_recording()
        assert not rec.is_recording()
        assert macro.meta.screen_width == 1920
        assert macro.meta.screen_height == 1080
        assert macro.is_edited is False

    def test_pause_resume_state_and_stop_while_paused(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import macroflow.win32 as w32

        monkeypatch.setattr(w32, "start_hook", lambda q: None)
        monkeypatch.setattr(w32, "stop_hook", lambda: None)
        monkeypatch.setattr(rec, "get_logical_screen_size", lambda: (1920, 1080))
        clock = iter(
            (1_000_000_000, 1_500_000_000, 4_500_000_000, 5_000_000_000, 5_500_000_000)
        )
        monkeypatch.setattr(rec.time, "perf_counter_ns", lambda: next(clock))

        rec.start_recording()
        assert rec.pause_recording()
        assert rec.is_paused()
        assert not rec.pause_recording()
        assert rec.resume_recording()
        assert not rec.is_paused()
        assert not rec.resume_recording()
        assert rec.pause_recording()

        macro = rec.stop_recording()

        assert not rec.is_paused()
        assert macro.events == []

    def test_events_injected_to_queue(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """큐에 주입한 이벤트가 MacroData에 포함되어야 한다."""
        import macroflow.win32 as w32

        monkeypatch.setattr(w32, "start_hook", lambda q: None)
        monkeypatch.setattr(w32, "stop_hook", lambda: None)
        monkeypatch.setattr(w32, "get_logical_screen_size", lambda: (1920, 1080))
        monkeypatch.setattr(w32, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))

        rec.start_recording()

        # 큐에 이벤트 직접 주입
        assert rec._raw_queue is not None
        rec._raw_queue.append(("m", rec._rec_start_ns + 100_000_000, 0x0201, (960, 540, 0)))
        rec._raw_queue.append(("m", rec._rec_start_ns + 200_000_000, 0x0202, (960, 540, 0)))
        rec._raw_queue.append(("k", rec._rec_start_ns + 300_000_000, 0x0100, (0x41, 0, 0)))

        # 소비자 스레드가 처리할 시간을 준다
        time.sleep(0.05)

        macro = rec.stop_recording()

        types = [e.type for e in macro.events]
        assert "mouse_down" in types
        assert "mouse_up" in types
        assert "key_down" in types

    def test_raw_events_equals_events_after_stop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """녹화 직후 raw_events와 events는 동일 내용이어야 한다 (is_edited=False)."""
        import macroflow.win32 as w32

        monkeypatch.setattr(w32, "start_hook", lambda q: None)
        monkeypatch.setattr(w32, "stop_hook", lambda: None)
        monkeypatch.setattr(w32, "get_logical_screen_size", lambda: (1920, 1080))
        monkeypatch.setattr(w32, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))

        rec.start_recording()
        time.sleep(0.02)
        macro = rec.stop_recording()

        assert macro.is_edited is False
        assert len(macro.raw_events) == len(macro.events)
        assert macro.events is not macro.raw_events  # 독립된 복사본

    def test_inject_color_trigger_accepts_configured_timeout_and_interval(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """녹화 중 F7 삽입 색 트리거는 현재 매크로 설정값을 보존할 수 있어야 한다."""
        import macroflow.win32 as w32

        monkeypatch.setattr(w32, "start_hook", lambda q: None)
        monkeypatch.setattr(w32, "stop_hook", lambda: None)
        monkeypatch.setattr(w32, "get_logical_screen_size", lambda: (1920, 1080))
        monkeypatch.setattr(rec, "get_logical_screen_size", lambda: (1920, 1080))

        rec.start_recording()
        rec.inject_color_trigger(
            0.25,
            0.5,
            "#112233",
            timeout_ms=8000,
            check_interval_ms=25,
        )

        macro = rec.stop_recording()

        event = macro.events[0]
        assert isinstance(event, ColorTriggerEvent)
        assert event.timeout_ms == 8000
        assert event.check_interval_ms == 25
