"""Playback lifecycle and range-progress regression tests."""

from __future__ import annotations

import threading
import time
from collections.abc import Generator

import pytest

from macroflow import player
from macroflow.types import (
    AnyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    WaitEvent,
)


def _make_macro(
    events: list[AnyEvent],
    *,
    settings: MacroSettings | None = None,
) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="test",
            created_at="2026-07-13T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=settings or MacroSettings(),
        raw_events=[],
        events=events,
    )


@pytest.fixture(autouse=True)
def _reset_player() -> Generator[None, None, None]:
    player._stop_flag.set()
    thread = player._playback_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=1.0)
    player._stop_flag.clear()
    yield
    player._stop_flag.set()
    thread = player._playback_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=1.0)
    player._stop_flag.clear()


def test_stop_interrupts_wait_event_without_post_stop_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered_wait = threading.Event()
    executed: list[str] = []
    completed: list[bool] = []
    original_execute = player._execute_event

    def _mark_wait_entered(
        event: AnyEvent,
        settings: MacroSettings,
        state: player._PlayState,
    ) -> None:
        if isinstance(event, WaitEvent):
            entered_wait.set()
        original_execute(event, settings, state)

    monkeypatch.setattr(player, "_execute_event", _mark_wait_entered)
    macro = _make_macro(
        [
            WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=500),
        ]
    )

    player.play(
        macro,
        on_event=lambda _idx, event: executed.append(event.id),
        on_complete=lambda: completed.append(True),
    )
    assert entered_wait.wait(timeout=0.5)

    started = time.perf_counter()
    player.stop()
    elapsed = time.perf_counter() - started

    assert elapsed < 0.2
    assert not player.is_playing()
    assert executed == []
    assert completed == []


def test_event_range_progress_is_relative_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(player, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(player, "send_mouse_move", lambda _x, _y: None)
    events: list[AnyEvent] = [
        MouseMoveEvent(
            id=f"event-{idx}",
            type="mouse_move",
            timestamp_ns=0,
            x_ratio=0.0,
            y_ratio=0.0,
        )
        for idx in range(7)
    ]
    progress: list[tuple[int, float]] = []
    completed = threading.Event()

    player.play(
        _make_macro(events),
        event_range=(5, 7),
        on_event=lambda idx, _event: progress.append((idx, player.get_progress())),
        on_complete=completed.set,
    )

    assert completed.wait(timeout=1.0)
    assert progress == [(5, 0.5), (6, 1.0)]
    assert all(0.0 <= value <= 1.0 for _, value in progress)


def test_stop_interrupts_scheduled_gap_before_next_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_executed = threading.Event()
    moves: list[tuple[int, int]] = []
    monkeypatch.setattr(player, "ratio_to_pixel", lambda x, y: (int(x), int(y)))
    monkeypatch.setattr(player, "send_mouse_move", lambda x, y: moves.append((x, y)))
    macro = _make_macro(
        [
            MouseMoveEvent(
                id="first",
                type="mouse_move",
                timestamp_ns=0,
                x_ratio=1.0,
                y_ratio=1.0,
            ),
            MouseMoveEvent(
                id="second",
                type="mouse_move",
                timestamp_ns=500_000_000,
                x_ratio=2.0,
                y_ratio=2.0,
            ),
        ]
    )

    player.play(
        macro,
        on_event=lambda idx, _event: first_executed.set() if idx == 0 else None,
    )
    assert first_executed.wait(timeout=0.5)
    time.sleep(0.05)
    assert player.get_progress() == 0.5

    started = time.perf_counter()
    player.stop()
    elapsed = time.perf_counter() - started

    assert elapsed < 0.2
    assert moves == [(1, 1)]


def test_play_rejects_overlapping_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    entered_wait = threading.Event()
    original_execute = player._execute_event

    def _mark_wait_entered(
        event: AnyEvent,
        settings: MacroSettings,
        state: player._PlayState,
    ) -> None:
        if isinstance(event, WaitEvent):
            entered_wait.set()
        original_execute(event, settings, state)

    monkeypatch.setattr(player, "_execute_event", _mark_wait_entered)
    macro = _make_macro(
        [
            WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=500),
        ]
    )
    player.play(macro)
    assert entered_wait.wait(timeout=0.5)

    with pytest.raises(player.PlaybackError, match="이미 재생 중"):
        player.play(macro)


def test_play_allows_terminal_worker_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_callback_started = threading.Event()
    second_completed = threading.Event()
    monkeypatch.setattr(player, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(player, "send_mouse_move", lambda _x, _y: None)
    macro = _make_macro(
        [
            MouseMoveEvent(
                id="event",
                type="mouse_move",
                timestamp_ns=0,
                x_ratio=0.0,
                y_ratio=0.0,
            ),
        ]
    )

    def _first_complete() -> None:
        first_callback_started.set()
        time.sleep(0.05)

    player.play(macro, on_complete=_first_complete)
    assert first_callback_started.wait(timeout=0.5)

    player.play(macro, on_complete=second_completed.set)

    assert second_completed.wait(timeout=0.5)


def test_user_stop_during_click_color_wait_does_not_emit_mismatch_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered_color_check = threading.Event()
    errors: list[str] = []
    monkeypatch.setattr(player, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(player, "send_mouse_move", lambda _x, _y: None)

    def _get_pixel_color(_x: int, _y: int) -> tuple[int, int, int]:
        entered_color_check.set()
        return (0, 0, 0)

    monkeypatch.setattr(player, "get_pixel_color", _get_pixel_color)
    macro = _make_macro(
        [
            MouseButtonEvent(
                id="click",
                type="mouse_down",
                timestamp_ns=0,
                x_ratio=0.0,
                y_ratio=0.0,
                button="left",
                recorded_color="#FFFFFF",
                color_check_enabled=True,
                color_check_on_mismatch="stop",
            )
        ],
        settings=MacroSettings(
            color_check_click_stop_timeout_ms=500,
            color_check_click_interval_ms=500,
        ),
    )
    player.play(macro, on_error=lambda exc: errors.append(str(exc)))
    assert entered_color_check.wait(timeout=0.5)

    player.stop()

    assert errors == []
