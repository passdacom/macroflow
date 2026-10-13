"""All playback entry points must reject invalid data before launching a worker."""

from __future__ import annotations

import copy
import threading
from collections.abc import Callable

import pytest

from macroflow import player
from macroflow.types import KeyEvent, LoopEvent, MacroData, MacroMeta, MacroSettings


def _macro() -> MacroData:
    return MacroData(
        meta=MacroMeta(version="1.0", app_version="test", created_at="",
                       screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(), raw_events=[],
        events=[KeyEvent(id="down", type="key_down", timestamp_ns=0, key="a", vk_code=65)],
    )


@pytest.mark.parametrize("speed", [0, -1, float("nan"), float("inf"), True])
def test_invalid_speed_is_rejected_without_worker_or_input(
    monkeypatch: pytest.MonkeyPatch, speed: float,
) -> None:
    called = threading.Event()
    monkeypatch.setattr(player, "_play_loop", lambda *args, **kwargs: called.set())
    prior_session = player._playback_session
    prior_thread = player._playback_thread
    with pytest.raises(ValueError, match="speed"):
        player.play(_macro(), speed=speed)
    assert not called.is_set()
    assert player._playback_session is prior_session
    assert player._playback_thread is prior_thread


def _bad_nested_key(macro: MacroData) -> None:
    macro.events.append(LoopEvent(id="loop", type="loop", timestamp_ns=0, count=1, events=[
        KeyEvent(id="bad", type="key_down", timestamp_ns=0, key="bad", vk_code=999),
    ]))


def _bad_later_timestamp(macro: MacroData) -> None:
    macro.events.append(KeyEvent(id="bad", type="key_up", timestamp_ns=10**400, key="a", vk_code=65))


def _bad_settings(macro: MacroData) -> None:
    macro.settings.color_check_click_interval_ms = 0


@pytest.mark.parametrize("mutate", [_bad_nested_key, _bad_later_timestamp, _bad_settings])
def test_whole_document_is_validated_before_even_first_valid_input(
    monkeypatch: pytest.MonkeyPatch, mutate: Callable[[MacroData], None],
) -> None:
    macro = _macro()
    mutate(macro)
    snapshot = copy.deepcopy(macro)
    called = threading.Event()
    monkeypatch.setattr(player, "_play_loop", lambda *args, **kwargs: called.set())
    with pytest.raises(ValueError):
        player.play(macro)
    assert not called.is_set()
    assert macro == snapshot
