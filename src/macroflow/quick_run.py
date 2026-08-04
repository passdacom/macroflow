"""Persistent five-slot configuration for one-shot quick macro playback."""

from __future__ import annotations

import math
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from macroflow.hotkey_config import hotkey_config_recovery_is_armed

QUICK_RUN_SLOT_COUNT = 5
QUICK_RUN_MIN_SPEED = 0.1
QUICK_RUN_MAX_SPEED = 10.0


class SettingsStore(Protocol):
    def value(self, key: str, default: object = None) -> object: ...

    def setValue(self, key: str, value: object) -> None: ...  # noqa: N802

    def remove(self, key: str) -> None: ...


@dataclass(frozen=True)
class QuickRunSlot:
    index: int
    name: str
    macro_path: Path | None = None
    speed: float = 1.0

    def __post_init__(self) -> None:
        if not 1 <= self.index <= QUICK_RUN_SLOT_COUNT:
            raise ValueError("quick-run slot index must be 1..5")
        normalized_name = self.name.strip() or f"슬롯 {self.index}"
        normalized_path = (
            self.macro_path.expanduser().resolve(strict=False)
            if self.macro_path is not None
            else None
        )
        if (
            isinstance(self.speed, bool)
            or not isinstance(self.speed, (int, float))
            or not math.isfinite(self.speed)
            or not QUICK_RUN_MIN_SPEED <= self.speed <= QUICK_RUN_MAX_SPEED
        ):
            raise ValueError("quick-run speed must be between 0.1x and 10.0x")
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "macro_path", normalized_path)
        object.__setattr__(self, "speed", float(self.speed))

    @property
    def action_id(self) -> str:
        return f"quick_run.slot_{self.index}"


def default_quick_run_slots() -> tuple[QuickRunSlot, ...]:
    return tuple(
        QuickRunSlot(index=index, name=f"슬롯 {index}")
        for index in range(1, QUICK_RUN_SLOT_COUNT + 1)
    )


def _value(
    settings: Mapping[str, object] | SettingsStore,
    key: str,
    default: object,
) -> object:
    if isinstance(settings, Mapping):
        return settings.get(key, default)
    return settings.value(key, default)


def _set_value(
    settings: MutableMapping[str, object] | SettingsStore,
    key: str,
    value: object,
) -> None:
    if isinstance(settings, MutableMapping):
        settings[key] = value
    else:
        settings.setValue(key, value)


def _remove_value(
    settings: MutableMapping[str, object] | SettingsStore,
    key: str,
) -> None:
    if isinstance(settings, MutableMapping):
        settings.pop(key, None)
    else:
        settings.remove(key)


def _sync_succeeded(settings: object) -> bool:
    sync = getattr(settings, "sync", None)
    if callable(sync):
        sync()
    status = getattr(settings, "status", None)
    if not callable(status):
        return True
    raw_status = status()
    status_value = getattr(raw_status, "value", raw_status)
    return int(str(status_value)) == 0


def _readback_matches(key: str, actual: object, expected: object) -> bool:
    if not key.endswith("/speed"):
        return actual == expected
    if isinstance(actual, bool) or not isinstance(actual, (str, int, float)):
        return False
    try:
        return float(actual) == expected
    except (OverflowError, ValueError):
        return False


def load_quick_run_slots(
    settings: Mapping[str, object] | SettingsStore,
    *,
    honor_recovery: bool = True,
) -> tuple[QuickRunSlot, ...]:
    slots: list[QuickRunSlot] = []
    recovery_prefix = (
        "quick_run/recovery"
        if honor_recovery and hotkey_config_recovery_is_armed(settings)
        else "quick_run"
    )
    for index in range(1, QUICK_RUN_SLOT_COUNT + 1):
        prefix = f"{recovery_prefix}/slot_{index}"
        raw_name = str(_value(settings, f"{prefix}/name", f"슬롯 {index}"))
        raw_path = str(_value(settings, f"{prefix}/path", ""))
        raw_speed = _value(settings, f"{prefix}/speed", 1.0)
        try:
            speed = (
                float(raw_speed)
                if isinstance(raw_speed, (str, int, float))
                and not isinstance(raw_speed, bool)
                else 1.0
            )
            if not math.isfinite(speed) or not QUICK_RUN_MIN_SPEED <= speed <= QUICK_RUN_MAX_SPEED:
                speed = 1.0
        except (OverflowError, ValueError):
            speed = 1.0
        try:
            path = Path(raw_path) if raw_path else None
            slots.append(
                QuickRunSlot(
                    index=index,
                    name=raw_name,
                    macro_path=path,
                    speed=speed,
                )
            )
        except (OSError, RuntimeError, TypeError, ValueError):
            slots.append(QuickRunSlot(index=index, name=f"슬롯 {index}"))
    return tuple(slots)


def arm_quick_run_recovery(
    settings: MutableMapping[str, object] | SettingsStore,
    slots: Sequence[QuickRunSlot],
) -> bool:
    """Stage the old slot set before the shared hotkey transaction marker is armed."""
    if len(slots) != QUICK_RUN_SLOT_COUNT or [slot.index for slot in slots] != list(
        range(1, QUICK_RUN_SLOT_COUNT + 1)
    ):
        raise ValueError("quick-run slots must contain ordered indices 1..5")
    expected: dict[str, object] = {}
    for slot in slots:
        prefix = f"quick_run/recovery/slot_{slot.index}"
        expected[f"{prefix}/name"] = slot.name
        expected[f"{prefix}/path"] = (
            str(slot.macro_path) if slot.macro_path is not None else ""
        )
        expected[f"{prefix}/speed"] = slot.speed
    try:
        for key, value in expected.items():
            _set_value(settings, key, value)
        if not _sync_succeeded(settings):
            return False
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    return all(
        _readback_matches(key, _value(settings, key, object()), value)
        for key, value in expected.items()
    )


def save_quick_run_slots(
    settings: MutableMapping[str, object] | SettingsStore,
    slots: Sequence[QuickRunSlot],
) -> bool:
    if len(slots) != QUICK_RUN_SLOT_COUNT or [slot.index for slot in slots] != list(
        range(1, QUICK_RUN_SLOT_COUNT + 1)
    ):
        raise ValueError("quick-run slots must contain ordered indices 1..5")
    missing = object()
    keys = tuple(
        f"quick_run/slot_{index}/{field}"
        for index in range(1, QUICK_RUN_SLOT_COUNT + 1)
        for field in ("name", "path", "speed")
    )
    snapshot = {key: _value(settings, key, missing) for key in keys}
    success = False
    try:
        for slot in slots:
            prefix = f"quick_run/slot_{slot.index}"
            _set_value(settings, f"{prefix}/name", slot.name)
            _set_value(
                settings,
                f"{prefix}/path",
                str(slot.macro_path) if slot.macro_path is not None else "",
            )
            _set_value(settings, f"{prefix}/speed", slot.speed)
        success = _sync_succeeded(settings)
        if success:
            success = load_quick_run_slots(settings, honor_recovery=False) == tuple(slots)
    except (OSError, RuntimeError, TypeError, ValueError):
        success = False
    if success:
        return True

    try:
        for key, value in snapshot.items():
            if value is missing:
                _remove_value(settings, key)
            else:
                _set_value(settings, key, value)
        _sync_succeeded(settings)
    except (OSError, RuntimeError, TypeError, ValueError):
        pass
    return False
