"""Pure policy, validation, and persistence helpers for configurable hotkeys."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Literal, Protocol, cast

HotkeyScope = Literal["runtime", "editor"]


class SettingsReader(Protocol):
    def value(self, key: str, default: object = None) -> object: ...


class SettingsWriter(Protocol):
    def setValue(self, key: str, value: object) -> None: ...  # noqa: N802 - QSettings API


class SettingsStore(SettingsReader, SettingsWriter, Protocol):
    pass


@dataclass(frozen=True)
class HotkeySpec:
    action_id: str
    scope: HotkeyScope
    default: str
    label: str

    @property
    def settings_key(self) -> str:
        return f"hotkeys/{self.action_id}"


HOTKEY_SPECS: Final = (
    HotkeySpec("runtime.record_or_capture", "runtime", "F6", "녹화 / 위치 캡처"),
    HotkeySpec("runtime.play_or_color_capture", "runtime", "F7", "재생 / 색상 캡처"),
    HotkeySpec("runtime.pause_or_resume", "runtime", "F8", "일시정지 / 계속"),
    HotkeySpec("recording.quick_text", "runtime", "F9", "빠른 텍스트 입력"),
    HotkeySpec("editor.insert_text", "editor", "Ctrl+Shift+T", "에디터 텍스트 추가"),
    HotkeySpec("editor.insert_click", "editor", "Ctrl+Shift+L", "에디터 클릭 추가"),
    HotkeySpec(
        "editor.insert_color_trigger",
        "editor",
        "Ctrl+Shift+G",
        "에디터 색 체크 삽입",
    ),
)
_SPEC_BY_ACTION: Final = {spec.action_id: spec for spec in HOTKEY_SPECS}
RUNTIME_ACTION_IDS: Final = tuple(
    spec.action_id for spec in HOTKEY_SPECS if spec.scope == "runtime"
)
EDITOR_ACTION_IDS: Final = tuple(spec.action_id for spec in HOTKEY_SPECS if spec.scope == "editor")
_RECOVERY_PREFIX: Final = "hotkeys/recovery/"
_RECOVERY_ARMED_KEY: Final = "hotkeys/recovery_armed"

_MODIFIER_NAMES: Final = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
    "windows": "Win",
    "meta": "Win",
    "super": "Win",
}
_MODIFIER_ORDER: Final = ("Ctrl", "Alt", "Shift", "Win")
_NAMED_KEYS: Final = {
    "delete": "Delete",
    "del": "Delete",
    "escape": "Esc",
    "esc": "Esc",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "space": "Space",
    "tab": "Tab",
    "backspace": "Backspace",
    "enter": "Enter",
    "return": "Enter",
}
_FIXED_EDITOR_SHORTCUTS: Final = frozenset(
    {
        "Ctrl+O",
        "Ctrl+S",
        "Ctrl+Shift+S",
        "Ctrl+Z",
        "Ctrl+Y",
        "Ctrl+Shift+Z",
        "Ctrl+D",
        "Delete",
    }
)


@dataclass(frozen=True)
class HotkeyConfig:
    """Immutable action-to-canonical-key mapping."""

    bindings: Mapping[str, str]

    def __post_init__(self) -> None:
        unknown = set(self.bindings) - set(_SPEC_BY_ACTION)
        if unknown:
            raise KeyError(next(iter(sorted(unknown))))
        values = {
            spec.action_id: str(self.bindings.get(spec.action_id, spec.default))
            for spec in HOTKEY_SPECS
        }
        object.__setattr__(self, "bindings", MappingProxyType(values))

    def binding_for(self, action_id: str) -> str:
        return self.bindings[action_id]

    def with_bindings(self, replacements: Mapping[str, str]) -> HotkeyConfig:
        unknown = set(replacements) - set(_SPEC_BY_ACTION)
        if unknown:
            raise KeyError(next(iter(sorted(unknown))))
        values = dict(self.bindings)
        values.update({action: _canonicalize_if_possible(value) for action, value in replacements.items()})
        return HotkeyConfig(values)


@dataclass(frozen=True)
class HotkeyValidationError:
    action_id: str
    message: str


@dataclass(frozen=True)
class HotkeyValidationResult:
    errors: tuple[HotkeyValidationError, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


DEFAULT_HOTKEY_CONFIG: Final = HotkeyConfig(
    {spec.action_id: spec.default for spec in HOTKEY_SPECS}
)


def _parse_chord(value: str) -> tuple[tuple[str, ...], str]:
    stripped = value.strip()
    if "," in stripped:
        raise ValueError("must be a single chord")
    parts = [part.strip() for part in stripped.split("+")]
    if not stripped or any(not part for part in parts):
        raise ValueError("invalid key sequence")

    modifiers: set[str] = set()
    keys: list[str] = []
    for part in parts:
        modifier = _MODIFIER_NAMES.get(part.casefold())
        if modifier is not None:
            if modifier in modifiers:
                raise ValueError("duplicate modifier")
            modifiers.add(modifier)
            continue
        folded = part.casefold()
        if folded.startswith("f") and folded[1:].isdigit():
            number = int(folded[1:])
            key = f"F{number}" if 1 <= number <= 24 else part.upper()
        elif len(part) == 1 and part.isprintable():
            key = part.upper()
        elif folded in _NAMED_KEYS:
            key = _NAMED_KEYS[folded]
        else:
            raise ValueError("unsupported key")
        keys.append(key)

    if len(keys) != 1:
        raise ValueError("must contain exactly one key")
    ordered_modifiers = tuple(name for name in _MODIFIER_ORDER if name in modifiers)
    return ordered_modifiers, keys[0]


def canonicalize_hotkey(value: str) -> str:
    """Return a stable display/QKeySequence string for one key chord."""
    if not value.strip():
        return ""
    modifiers, key = _parse_chord(value)
    return "+".join((*modifiers, key))


def _canonicalize_if_possible(value: str) -> str:
    try:
        return canonicalize_hotkey(str(value))
    except ValueError:
        return str(value).strip()


def validate_hotkey_config(config: HotkeyConfig) -> HotkeyValidationResult:
    """Validate all configurable bindings and report action-specific errors."""
    errors: list[HotkeyValidationError] = []
    canonical: dict[str, str] = {}

    for spec in HOTKEY_SPECS:
        value = config.binding_for(spec.action_id)
        if not value.strip():
            if spec.scope == "runtime":
                errors.append(HotkeyValidationError(spec.action_id, "runtime binding is required"))
            canonical[spec.action_id] = ""
            continue
        try:
            modifiers, key = _parse_chord(value)
        except ValueError as exc:
            errors.append(HotkeyValidationError(spec.action_id, str(exc)))
            continue

        chord = "+".join((*modifiers, key))
        canonical[spec.action_id] = chord
        if "Win" in modifiers:
            errors.append(HotkeyValidationError(spec.action_id, "Windows-key combinations are reserved"))
            continue
        if chord in {"Esc", "Alt+F4", "Ctrl+Alt+Delete"}:
            errors.append(HotkeyValidationError(spec.action_id, "shortcut is reserved for safety"))
            continue
        function_number = int(key[1:]) if key.startswith("F") and key[1:].isdigit() else None
        if function_number is not None and not 1 <= function_number <= 24:
            errors.append(HotkeyValidationError(spec.action_id, "function key must be F1..F24"))
            continue
        if spec.scope == "runtime":
            if function_number == 12:
                errors.append(
                    HotkeyValidationError(spec.action_id, "F12 is reserved by Windows")
                )
            elif modifiers or function_number is None:
                errors.append(
                    HotkeyValidationError(spec.action_id, "runtime binding must be a bare F1..F24 key")
                )
        else:
            if chord in _FIXED_EDITOR_SHORTCUTS:
                errors.append(
                    HotkeyValidationError(spec.action_id, "shortcut conflicts with a fixed shortcut")
                )
            elif not modifiers and function_number is None:
                errors.append(
                    HotkeyValidationError(
                        spec.action_id, "non-function editor keys require a modifier"
                    )
                )

    by_chord: dict[str, list[str]] = {}
    for action_id, chord in canonical.items():
        if chord:
            by_chord.setdefault(chord, []).append(action_id)
    for chord, action_ids in by_chord.items():
        if len(action_ids) > 1:
            errors.extend(
                HotkeyValidationError(action_id, f"duplicate configurable binding: {chord}")
                for action_id in action_ids
            )

    return HotkeyValidationResult(tuple(errors))


def runtime_virtual_keys(config: HotkeyConfig) -> frozenset[int]:
    """Return active runtime Win32 virtual-key codes for recorder filtering."""
    result = validate_hotkey_config(config)
    if not result.is_valid:
        raise ValueError("cannot derive virtual keys from invalid hotkey config")
    return frozenset(0x70 + int(config.binding_for(action)[1:]) - 1 for action in RUNTIME_ACTION_IDS)


def _settings_value(
    settings: Mapping[str, object] | SettingsReader, key: str, default: str
) -> object:
    if isinstance(settings, Mapping):
        return settings.get(key, default)
    return settings.value(key, default)


def _settings_set(
    settings: MutableMapping[str, object] | SettingsWriter,
    key: str,
    value: object,
) -> None:
    if isinstance(settings, MutableMapping):
        settings[key] = value
    else:
        settings.setValue(key, value)


def _settings_sync_succeeded(settings: object) -> bool:
    try:
        sync = getattr(settings, "sync", None)
        if callable(sync):
            sync()
        status = getattr(settings, "status", None)
        if callable(status):
            raw_status = status()
            if int(cast(Any, getattr(raw_status, "value", raw_status))) != 0:
                return False
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    return True


def _recovery_key(action_id: str) -> str:
    return f"{_RECOVERY_PREFIX}{action_id}"


def _recovery_is_armed(settings: Mapping[str, object] | SettingsReader) -> bool:
    raw = _settings_value(settings, _RECOVERY_ARMED_KEY, "false")
    if isinstance(raw, str):
        return raw.strip().casefold() in {"1", "true", "yes", "on"}
    return bool(raw)


def arm_hotkey_config_recovery(
    settings: MutableMapping[str, object] | SettingsStore,
    config: HotkeyConfig,
) -> bool:
    """Durably arm a last-known-good snapshot before changing active settings."""
    try:
        for spec in HOTKEY_SPECS:
            _settings_set(
                settings,
                _recovery_key(spec.action_id),
                config.binding_for(spec.action_id),
            )
        _settings_set(settings, _RECOVERY_ARMED_KEY, True)
        if not _settings_sync_succeeded(settings) or not _recovery_is_armed(settings):
            return False
        return all(
            _settings_value(settings, _recovery_key(spec.action_id), "")
            == config.binding_for(spec.action_id)
            for spec in HOTKEY_SPECS
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def disarm_hotkey_config_recovery(
    settings: MutableMapping[str, object] | SettingsStore,
) -> bool:
    """Commit active settings by durably clearing the recovery marker."""
    try:
        _settings_set(settings, _RECOVERY_ARMED_KEY, False)
        return _settings_sync_succeeded(settings) and not _recovery_is_armed(settings)
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def load_hotkey_config(settings: Mapping[str, object] | SettingsReader) -> HotkeyConfig:
    """Load a valid config, returning defaults for any corrupt persisted set."""
    if _recovery_is_armed(settings):
        recovered_values = {
            spec.action_id: _canonicalize_if_possible(
                str(_settings_value(settings, _recovery_key(spec.action_id), ""))
            )
            for spec in HOTKEY_SPECS
        }
        recovered = HotkeyConfig(recovered_values)
        return recovered if validate_hotkey_config(recovered).is_valid else DEFAULT_HOTKEY_CONFIG

    values = {
        spec.action_id: _canonicalize_if_possible(
            str(_settings_value(settings, spec.settings_key, spec.default))
        )
        for spec in HOTKEY_SPECS
    }
    config = HotkeyConfig(values)
    return config if validate_hotkey_config(config).is_valid else DEFAULT_HOTKEY_CONFIG


def save_hotkey_config(
    settings: MutableMapping[str, object] | SettingsStore, config: HotkeyConfig
) -> bool:
    """Persist and read back a valid config; return False on storage failure."""
    result = validate_hotkey_config(config)
    if not result.is_valid:
        raise ValueError("cannot save invalid hotkey config")
    expected = {
        spec.settings_key: canonicalize_hotkey(config.binding_for(spec.action_id))
        for spec in HOTKEY_SPECS
    }
    try:
        for key, value in expected.items():
            _settings_set(settings, key, value)
        if not _settings_sync_succeeded(settings):
            return False
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    return all(
        str(_settings_value(settings, key, "")) == value
        for key, value in expected.items()
    )
