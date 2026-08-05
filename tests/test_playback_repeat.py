"""Repeat playback orchestration helpers."""

from __future__ import annotations

from macroflow.ui.playback_repeat import (
    PlaybackStartOptions,
    RepeatPlaybackSession,
    full_playback_options,
    range_playback_options,
)


def test_stop_request_prevents_later_cycles() -> None:
    session = RepeatPlaybackSession(total=10)

    assert session.should_start_cycle(0)
    session.request_stop()

    assert not session.should_start_cycle(5)
    assert session.was_stopped


def test_stop_request_releases_polling_after_player_exits() -> None:
    session = RepeatPlaybackSession(total=10)
    session.mark_started()
    session.mark_between_cycles()
    session.request_stop()

    assert not session.should_poll_wait_for_worker(player_is_playing=False)


def test_repeat_session_stays_active_between_cycles() -> None:
    session = RepeatPlaybackSession(total=3)
    session.mark_started()
    session.mark_cycle_started(1)
    session.mark_between_cycles()

    assert session.is_active
    assert session.should_poll_wait_for_worker(player_is_playing=False)

    session.mark_finished()

    assert not session.is_active
    assert not session.should_poll_wait_for_worker(player_is_playing=False)


def test_cycle_label_uses_one_based_count() -> None:
    session = RepeatPlaybackSession(total=10)
    session.mark_cycle_started(2)

    assert session.cycle_label == "3/10회"


def test_full_playback_options_ignore_range_spinbox_values() -> None:
    options = full_playback_options(repeat_count=5)

    assert options == PlaybackStartOptions(
        event_range=None,
        repeat_count=5,
        confirm_repeat=True,
    )


def test_range_playback_options_force_single_repeat_without_confirmation() -> None:
    options = range_playback_options((2, 8))

    assert options == PlaybackStartOptions(
        event_range=(2, 8),
        repeat_count=1,
        confirm_repeat=False,
    )
