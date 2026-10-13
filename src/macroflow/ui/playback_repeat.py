"""Pure helpers for MacroFlow repeat playback session state.

This module is intentionally PyQt-free so repeat orchestration semantics can be
regression-tested without constructing the main window.
"""

from __future__ import annotations

import dataclasses

from macroflow.playback_controller import RepeatPlaybackSession as RepeatPlaybackSession


@dataclasses.dataclass(frozen=True)
class PlaybackStartOptions:
    """Normalized options for a playback start request."""

    event_range: tuple[int, int] | None
    repeat_count: int
    confirm_repeat: bool


def full_playback_options(repeat_count: int) -> PlaybackStartOptions:
    """Return options for normal F7/play-button playback.

    Normal playback deliberately ignores range spinbox values: range playback is
    only triggered by the explicit range-play button.
    """
    return PlaybackStartOptions(
        event_range=None,
        repeat_count=max(1, repeat_count),
        confirm_repeat=True,
    )


def range_playback_options(event_range: tuple[int, int]) -> PlaybackStartOptions:
    """Return options for explicit range playback.

    Range playback follows speed settings but never repeats and does not ask for
    repeat confirmation.
    """
    return PlaybackStartOptions(
        event_range=event_range,
        repeat_count=1,
        confirm_repeat=False,
    )
