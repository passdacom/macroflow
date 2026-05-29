"""Pure helpers for MacroFlow repeat playback session state.

This module is intentionally PyQt-free so repeat orchestration semantics can be
regression-tested without constructing the main window.
"""

from __future__ import annotations

import dataclasses
import threading


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


@dataclasses.dataclass
class RepeatPlaybackSession:
    """State for one full repeat playback request.

    `cycle_index` is zero-based internally; user-facing labels are one-based.
    """

    total: int
    cycle_index: int = 0
    is_active: bool = False
    _stop_requested: threading.Event = dataclasses.field(default_factory=threading.Event)

    def mark_started(self) -> None:
        """Mark the repeat worker as active."""
        self.is_active = True
        self._stop_requested.clear()
        self.cycle_index = 0

    def mark_cycle_started(self, cycle_index: int) -> None:
        """Update the currently running repeat cycle."""
        self.is_active = True
        self.cycle_index = cycle_index

    def mark_between_cycles(self) -> None:
        """Keep the session active while no player thread is alive between cycles."""
        self.is_active = True

    def mark_finished(self) -> None:
        """Mark repeat playback as fully finished."""
        self.is_active = False

    def request_stop(self) -> None:
        """Request complete repeat-session stop, not just current cycle stop."""
        self._stop_requested.set()

    @property
    def was_stopped(self) -> bool:
        """Return whether a complete repeat-session stop was requested."""
        return self._stop_requested.is_set()

    @property
    def cycle_label(self) -> str:
        """Return user-facing repeat cycle label, e.g. '3/10회'."""
        total = max(1, self.total)
        current = min(max(0, self.cycle_index) + 1, total)
        return f"{current}/{total}회"

    def should_start_cycle(self, cycle_index: int) -> bool:
        """Return True when the repeat worker may start the given cycle."""
        return not self._stop_requested.is_set() and cycle_index < self.total

    def should_poll_wait_for_worker(self, *, player_is_playing: bool) -> bool:
        """Return True when UI polling should not complete playback yet.

        During repeat playback, the single-cycle player can be briefly inactive
        between cycles. The UI must keep overlay/state alive until the repeat
        worker itself finishes.
        """
        return self.is_active and not player_is_playing
