"""recorder.py 이벤트 캡처 로직 테스트."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

import macroflow.recorder as rec
from macroflow.recorder import _convert_raw, _vk_to_key
from macroflow.types import KeyEvent, MouseButtonEvent, MouseMoveEvent

# ── _convert_raw 단위 테스트 ──────────────────────────────────────────────────

class TestConvertRaw:
    """_convert_raw 함수 — raw 이벤트 → MacroEvent 변환 테스트."""

    def setup_method(self) -> None:
        """녹화 시작 타임스탬프와 화면 크기를 설정한다."""
        rec._rec_start_ns = 0
        rec._screen_w = 1920
        rec._screen_h = 1080

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

    def test_event_id_is_8hex(self) -> None:
        """생성된 이벤트 id는 8자리 hex 문자열이어야 한다."""
        with patch("macroflow.recorder.pixel_to_ratio", return_value=(0.0, 0.0)):
            raw = ("m", 0, 0x0200, (0, 0, 0))
            event = _convert_raw(raw)

        assert event is not None
        assert len(event.id) == 8
        assert all(c in "0123456789abcdef" for c in event.id)


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
