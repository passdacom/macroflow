"""F9 quick-text playback-delay preference contracts."""

from __future__ import annotations

from macroflow.ui.quick_text_settings import (
    DEFAULT_QUICK_TEXT_DELAY_MS,
    QUICK_TEXT_DELAY_KEY,
    quick_text_delay_input,
    quick_text_delay_override,
)


class _FakeSettings:
    def __init__(self, value: object = None) -> None:
        self._value = value

    def value(self, key: str, default: object) -> object:
        assert key == QUICK_TEXT_DELAY_KEY
        return default if self._value is None else self._value


def test_quick_text_delay_defaults_to_safe_100ms() -> None:
    settings = _FakeSettings()

    assert DEFAULT_QUICK_TEXT_DELAY_MS == 100
    assert quick_text_delay_input(settings) == 100
    assert quick_text_delay_override(settings) == 100


def test_quick_text_delay_supports_recorded_timing_zero_and_positive_values() -> None:
    assert quick_text_delay_override(_FakeSettings("-1")) is None
    assert quick_text_delay_override(_FakeSettings("0")) == 0
    assert quick_text_delay_override(_FakeSettings("250")) == 250


def test_quick_text_delay_normalizes_corrupt_or_out_of_range_settings() -> None:
    assert quick_text_delay_input(_FakeSettings("bad")) == 100
    assert quick_text_delay_input(_FakeSettings(-99)) == -1
    assert quick_text_delay_input(_FakeSettings(999_999)) == 60_000
