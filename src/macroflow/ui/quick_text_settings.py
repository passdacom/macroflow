"""App-level preference for F9 semantic text playback delay."""

from __future__ import annotations

from typing import Any

QUICK_TEXT_DELAY_KEY = "quick_text_playback_delay_ms"
DEFAULT_QUICK_TEXT_DELAY_MS = 100
_MIN_QUICK_TEXT_DELAY_INPUT = -1
_MAX_QUICK_TEXT_DELAY_INPUT = 60_000


def quick_text_delay_input(settings: Any) -> int:
    """Return the persisted UI value normalized to ``-1..60000``."""
    raw = settings.value(QUICK_TEXT_DELAY_KEY, DEFAULT_QUICK_TEXT_DELAY_MS)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = DEFAULT_QUICK_TEXT_DELAY_MS
    return min(_MAX_QUICK_TEXT_DELAY_INPUT, max(_MIN_QUICK_TEXT_DELAY_INPUT, value))


def quick_text_delay_override(settings: Any) -> int | None:
    """Return the TextInputEvent override; ``-1`` selects recorded timing."""
    value = quick_text_delay_input(settings)
    return None if value < 0 else value
