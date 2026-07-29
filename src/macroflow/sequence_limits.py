"""Shared numeric contracts for sequencer-authored timing values."""

from __future__ import annotations

from typing import TypeGuard

MAX_SEQUENCE_WAIT_MS = 30_000


def is_sequence_wait_duration(value: object) -> TypeGuard[int]:
    """Return whether value can be represented by the sequencer wait control."""
    return type(value) is int and 0 <= value <= MAX_SEQUENCE_WAIT_MS
