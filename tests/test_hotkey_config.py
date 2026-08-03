from __future__ import annotations

from typing import Any

import pytest

from macroflow.hotkey_config import (
    DEFAULT_HOTKEY_CONFIG,
    HotkeyConfig,
    arm_hotkey_config_recovery,
    disarm_hotkey_config_recovery,
    load_hotkey_config,
    runtime_virtual_keys,
    save_hotkey_config,
    validate_hotkey_config,
)


class FakeSettings:
    def __init__(self, values: dict[str, Any] | None = None) -> None:
        self.values = dict(values or {})
        self.writes: list[tuple[str, object]] = []

    def value(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def setValue(self, key: str, value: object) -> None:  # noqa: N802 - QSettings API
        self.values[key] = value
        self.writes.append((key, value))


def _config(**overrides: str) -> HotkeyConfig:
    return DEFAULT_HOTKEY_CONFIG.with_bindings(overrides)


def test_defaults_are_canonical_and_expose_runtime_virtual_keys() -> None:
    assert dict(DEFAULT_HOTKEY_CONFIG.bindings) == {
        "runtime.record_or_capture": "F6",
        "runtime.play_or_color_capture": "F7",
        "runtime.pause_or_resume": "F8",
        "recording.quick_text": "F9",
        "editor.insert_text": "Ctrl+Shift+T",
        "editor.insert_click": "Ctrl+Shift+L",
        "editor.insert_color_trigger": "Ctrl+Shift+G",
        "quick_run.slot_1": "Ctrl+Alt+1",
        "quick_run.slot_2": "Ctrl+Alt+2",
        "quick_run.slot_3": "Ctrl+Alt+3",
        "quick_run.slot_4": "Ctrl+Alt+4",
        "quick_run.slot_5": "Ctrl+Alt+5",
    }
    assert runtime_virtual_keys(DEFAULT_HOTKEY_CONFIG) == frozenset({0x75, 0x76, 0x77, 0x78})


def test_load_uses_stable_settings_keys_and_does_not_write() -> None:
    settings = FakeSettings({"hotkeys/runtime.record_or_capture": "f13"})

    loaded = load_hotkey_config(settings)

    assert loaded.binding_for("runtime.record_or_capture") == "F13"
    assert loaded.binding_for("runtime.play_or_color_capture") == "F7"
    assert settings.writes == []


def test_load_supports_mapping_like_settings() -> None:
    loaded = load_hotkey_config({"hotkeys/editor.insert_text": " alt + t "})

    assert loaded.binding_for("editor.insert_text") == "Alt+T"


def test_armed_recovery_snapshot_wins_over_partially_persisted_candidate() -> None:
    settings = FakeSettings()
    old_config = DEFAULT_HOTKEY_CONFIG
    candidate = _config(**{"runtime.record_or_capture": "F10"})

    assert arm_hotkey_config_recovery(settings, old_config)
    assert save_hotkey_config(settings, candidate)
    assert load_hotkey_config(settings) == old_config

    assert disarm_hotkey_config_recovery(settings)
    assert load_hotkey_config(settings) == candidate


def test_corrupt_armed_recovery_fails_closed_to_defaults() -> None:
    settings = FakeSettings({"hotkeys/recovery_armed": True})

    assert load_hotkey_config(settings) == DEFAULT_HOTKEY_CONFIG


def test_corrupt_persisted_config_falls_back_to_defaults_without_mutating_settings() -> None:
    settings = FakeSettings(
        {
            "hotkeys/runtime.record_or_capture": "Ctrl+F6",
            "hotkeys/editor.insert_text": "T",
        }
    )

    loaded = load_hotkey_config(settings)

    assert loaded == DEFAULT_HOTKEY_CONFIG
    assert settings.writes == []


def test_save_writes_only_canonical_configurable_bindings() -> None:
    settings: dict[str, str] = {}
    config = _config(
        **{
            "runtime.record_or_capture": "F10",
            "editor.insert_text": "",
        }
    )

    assert save_hotkey_config(settings, config) is True

    assert settings == {
        "hotkeys/runtime.record_or_capture": "F10",
        "hotkeys/runtime.play_or_color_capture": "F7",
        "hotkeys/runtime.pause_or_resume": "F8",
        "hotkeys/recording.quick_text": "F9",
        "hotkeys/editor.insert_text": "",
        "hotkeys/editor.insert_click": "Ctrl+Shift+L",
        "hotkeys/editor.insert_color_trigger": "Ctrl+Shift+G",
        "hotkeys/quick_run.slot_1": "Ctrl+Alt+1",
        "hotkeys/quick_run.slot_2": "Ctrl+Alt+2",
        "hotkeys/quick_run.slot_3": "Ctrl+Alt+3",
        "hotkeys/quick_run.slot_4": "Ctrl+Alt+4",
        "hotkeys/quick_run.slot_5": "Ctrl+Alt+5",
    }


def test_save_reports_readback_failure() -> None:
    class UnwritableSettings(FakeSettings):
        def setValue(self, key: str, value: object) -> None:  # noqa: N802
            self.writes.append((key, value))

    settings = UnwritableSettings()

    assert save_hotkey_config(settings, DEFAULT_HOTKEY_CONFIG) is False


@pytest.mark.parametrize(
    ("overrides", "action_id", "reason"),
    [
        ({"runtime.record_or_capture": ""}, "runtime.record_or_capture", "required"),
        ({"runtime.record_or_capture": "Ctrl+F6"}, "runtime.record_or_capture", "bare F1..F24"),
        ({"runtime.record_or_capture": "A"}, "runtime.record_or_capture", "bare F1..F24"),
        ({"editor.insert_text": "T"}, "editor.insert_text", "modifier"),
        ({"editor.insert_text": "F25"}, "editor.insert_text", "F1..F24"),
        ({"editor.insert_text": "Ctrl+T, Ctrl+X"}, "editor.insert_text", "single chord"),
        ({"editor.insert_text": "Win+T"}, "editor.insert_text", "Windows-key"),
        ({"editor.insert_text": "Esc"}, "editor.insert_text", "reserved"),
        ({"editor.insert_text": "Alt+F4"}, "editor.insert_text", "reserved"),
        ({"editor.insert_text": "Ctrl+Alt+Delete"}, "editor.insert_text", "reserved"),
        ({"editor.insert_text": "Ctrl+S"}, "editor.insert_text", "fixed shortcut"),
        ({"editor.insert_text": "Delete"}, "editor.insert_text", "fixed shortcut"),
    ],
)
def test_invalid_bindings_are_rejected_for_the_owning_action(
    overrides: dict[str, str], action_id: str, reason: str
) -> None:
    result = validate_hotkey_config(_config(**overrides))

    assert not result.is_valid
    assert result.errors[0].action_id == action_id
    assert reason in result.errors[0].message


def test_duplicates_are_rejected_across_global_and_local_scopes() -> None:
    result = validate_hotkey_config(_config(**{"editor.insert_text": "F6"}))

    assert not result.is_valid
    assert {error.action_id for error in result.errors} == {
        "runtime.record_or_capture",
        "editor.insert_text",
    }
    assert all("duplicate" in error.message for error in result.errors)


def test_local_binding_may_be_cleared_and_function_keys_may_be_bare() -> None:
    config = _config(
        **{
            "editor.insert_text": "",
            "editor.insert_click": "F12",
        }
    )

    assert validate_hotkey_config(config).is_valid
    assert config.binding_for("editor.insert_click") == "F12"


def test_quick_run_bindings_are_global_modified_chords() -> None:
    config = _config(**{"quick_run.slot_1": "Shift+F10"})

    assert validate_hotkey_config(config).is_valid

    invalid = validate_hotkey_config(_config(**{"quick_run.slot_1": "1"}))
    assert not invalid.is_valid
    assert invalid.errors[0].action_id == "quick_run.slot_1"
    assert "modifier" in invalid.errors[0].message


def test_unknown_action_is_not_accepted() -> None:
    with pytest.raises(KeyError):
        DEFAULT_HOTKEY_CONFIG.with_bindings({"unknown.action": "F10"})


def test_windows_debugger_reserved_f12_is_rejected_for_runtime_hotkeys() -> None:
    config = _config(**{"runtime.record_or_capture": "F12"})

    result = validate_hotkey_config(config)

    assert not result.is_valid
    assert any(
        error.action_id == "runtime.record_or_capture"
        and error.message == "F12 is reserved by Windows"
        for error in result.errors
    )


def test_unknown_key_name_is_rejected_instead_of_creating_dead_qshortcut() -> None:
    config = _config(**{"editor.insert_text": "Ctrl+NotARealKey"})

    result = validate_hotkey_config(config)

    assert not result.is_valid
    assert any(
        error.action_id == "editor.insert_text"
        and error.message == "unsupported key"
        for error in result.errors
    )
