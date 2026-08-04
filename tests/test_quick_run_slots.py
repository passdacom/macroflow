from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from macroflow.hotkey_config import (
    DEFAULT_HOTKEY_CONFIG,
    arm_hotkey_config_recovery,
    disarm_hotkey_config_recovery,
)
from macroflow.quick_run import (
    QUICK_RUN_SLOT_COUNT,
    QuickRunSlot,
    arm_quick_run_recovery,
    default_quick_run_slots,
    load_quick_run_slots,
    save_quick_run_slots,
)


class FakeSettings:
    def __init__(self, values: dict[str, Any] | None = None) -> None:
        self.values = dict(values or {})

    def value(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def setValue(self, key: str, value: object) -> None:  # noqa: N802
        self.values[key] = value

    def remove(self, key: str) -> None:
        self.values.pop(key, None)

    def sync(self) -> None:
        return None

    def status(self) -> int:
        return 0


def test_default_quick_run_slots_are_five_named_empty_slots() -> None:
    slots = default_quick_run_slots()

    assert QUICK_RUN_SLOT_COUNT == 5
    assert [slot.index for slot in slots] == [1, 2, 3, 4, 5]
    assert [slot.name for slot in slots] == [f"슬롯 {index}" for index in range(1, 6)]
    assert [slot.macro_path for slot in slots] == [None] * 5
    assert [slot.speed for slot in slots] == [1.0] * 5
    assert [slot.action_id for slot in slots] == [
        f"quick_run.slot_{index}" for index in range(1, 6)
    ]


def test_quick_run_slots_round_trip_names_paths_and_speeds(tmp_path: Path) -> None:
    macro = tmp_path / "macros" / "step-one.json"
    macro.parent.mkdir()
    macro.write_text("{}", encoding="utf-8")
    slots = list(default_quick_run_slots())
    slots[0] = QuickRunSlot(
        index=1,
        name="공통 전처리",
        macro_path=macro,
        speed=2.5,
    )
    settings = FakeSettings()

    assert save_quick_run_slots(settings, tuple(slots))
    loaded = load_quick_run_slots(settings)

    assert loaded[0].name == "공통 전처리"
    assert loaded[0].macro_path == macro.resolve(strict=False)
    assert loaded[0].speed == 2.5
    assert loaded[1:] == default_quick_run_slots()[1:]


def test_legacy_quick_run_slots_without_speed_load_at_normal_speed() -> None:
    settings = FakeSettings(
        {
            "quick_run/slot_1/name": "기존 슬롯",
            "quick_run/slot_1/path": "/old/macro.json",
        }
    )

    loaded = load_quick_run_slots(settings)

    assert loaded[0].speed == 1.0


@pytest.mark.parametrize("speed", [0.0, 10.1, float("nan"), float("inf"), True])
def test_quick_run_slot_rejects_invalid_speed(speed: object) -> None:
    with pytest.raises(ValueError, match="speed"):
        QuickRunSlot(index=1, name="슬롯 1", speed=speed)  # type: ignore[arg-type]


def test_corrupt_slot_settings_fail_closed_to_an_empty_slot() -> None:
    settings = FakeSettings(
        {
            "quick_run/slot_1/name": "   ",
            "quick_run/slot_1/path": "\x00bad-path",
        }
    )

    loaded = load_quick_run_slots(settings)

    assert loaded[0] == QuickRunSlot(index=1, name="슬롯 1", macro_path=None)


def test_failed_slot_sync_restores_the_complete_previous_snapshot(tmp_path: Path) -> None:
    class FailingFirstSync(FakeSettings):
        def __init__(self, values: dict[str, Any]) -> None:
            super().__init__(values)
            self.sync_count = 0

        def sync(self) -> None:
            self.sync_count += 1

        def status(self) -> int:
            return 1 if self.sync_count == 1 else 0

    before = {
        "quick_run/slot_1/name": "기존 슬롯",
        "quick_run/slot_1/path": "/old/macro.json",
    }
    settings = FailingFirstSync(before)
    slots = list(default_quick_run_slots())
    slots[0] = QuickRunSlot(1, "새 슬롯", tmp_path / "new.json")

    assert not save_quick_run_slots(settings, tuple(slots))
    assert settings.values == before
    assert settings.sync_count == 2


def test_armed_shared_recovery_restores_matching_old_slots_until_commit(
    tmp_path: Path,
) -> None:
    old_slots = list(default_quick_run_slots())
    old_slots[0] = QuickRunSlot(1, "이전 슬롯", tmp_path / "old.json")
    new_slots = list(default_quick_run_slots())
    new_slots[0] = QuickRunSlot(1, "새 슬롯", tmp_path / "new.json")
    settings = FakeSettings()
    assert save_quick_run_slots(settings, tuple(old_slots))

    assert arm_quick_run_recovery(settings, tuple(old_slots))
    assert arm_hotkey_config_recovery(settings, DEFAULT_HOTKEY_CONFIG)
    assert save_quick_run_slots(settings, tuple(new_slots))

    assert load_quick_run_slots(settings) == tuple(old_slots)
    assert disarm_hotkey_config_recovery(settings)
    assert load_quick_run_slots(settings) == tuple(new_slots)


def test_recovery_accepts_qsettings_numeric_string_readback(tmp_path: Path) -> None:
    class StringifyingFloatSettings(FakeSettings):
        def value(self, key: str, default: Any = None) -> Any:
            value = super().value(key, default)
            if key.endswith("/speed") and isinstance(value, float):
                return str(value)
            return value

    slots = list(default_quick_run_slots())
    slots[0] = QuickRunSlot(1, "빠른 슬롯", tmp_path / "macro.json", 2.5)

    assert arm_quick_run_recovery(StringifyingFloatSettings(), tuple(slots))


def test_recovery_fails_closed_for_oversized_numeric_readback() -> None:
    class OversizedSpeedSettings(FakeSettings):
        def value(self, key: str, default: Any = None) -> Any:
            if key.endswith("/speed"):
                return 10**10_000
            return super().value(key, default)

    assert not arm_quick_run_recovery(
        OversizedSpeedSettings(),
        default_quick_run_slots(),
    )
