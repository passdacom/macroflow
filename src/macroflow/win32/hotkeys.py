"""Win32 global-hotkey registration with transactional set replacement."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final, Protocol

from macroflow.hotkey_config import (
    QUICK_RUN_ACTION_IDS,
    RUNTIME_ACTION_IDS,
    HotkeyConfig,
    parse_hotkey_chord,
    runtime_virtual_keys,
)

MOD_ALT: Final = 0x0001
MOD_CONTROL: Final = 0x0002
MOD_SHIFT: Final = 0x0004
MOD_NOREPEAT: Final = 0x4000
WM_HOTKEY: Final = 0x0312


@dataclass(frozen=True)
class NativeHotkey:
    action_id: str
    registration_id: int
    modifiers: int
    vk: int

    @property
    def display_key(self) -> str:
        names: list[str] = []
        if self.modifiers & MOD_CONTROL:
            names.append("Ctrl")
        if self.modifiers & MOD_ALT:
            names.append("Alt")
        if self.modifiers & MOD_SHIFT:
            names.append("Shift")
        if 0x70 <= self.vk <= 0x87:
            key = f"F{self.vk - 0x70 + 1}"
        elif 0x30 <= self.vk <= 0x39 or 0x41 <= self.vk <= 0x5A:
            key = chr(self.vk)
        else:
            key = f"VK_{self.vk:02X}"
        return "+".join((*names, key))


@dataclass(frozen=True)
class RegistrationResult:
    success: bool
    failed_action_id: str | None = None
    failed_key: str | None = None
    rollback_succeeded: bool = True


class HotkeyBackend(Protocol):
    def register_hotkey(self, registration_id: int, modifiers: int, vk: int) -> bool: ...

    def unregister_hotkey(self, registration_id: int) -> bool: ...


class HotkeyRegistrar(Protocol):
    @property
    def current(self) -> Sequence[NativeHotkey]: ...

    def replace(self, candidate: Sequence[NativeHotkey]) -> RegistrationResult: ...


def _native_key(value: str) -> tuple[int, int]:
    modifiers, key = parse_hotkey_chord(value)
    native_modifiers = MOD_NOREPEAT
    if "Ctrl" in modifiers:
        native_modifiers |= MOD_CONTROL
    if "Alt" in modifiers:
        native_modifiers |= MOD_ALT
    if "Shift" in modifiers:
        native_modifiers |= MOD_SHIFT
    if key.startswith("F") and key[1:].isdigit():
        vk = 0x70 + int(key[1:]) - 1
    elif len(key) == 1 and key.isalnum():
        vk = ord(key.upper())
    else:
        raise ValueError(f"unsupported global hotkey key: {key}")
    return native_modifiers, vk


def native_hotkeys(
    config: HotkeyConfig,
    *,
    include_quick_run: bool = True,
) -> tuple[NativeHotkey, ...]:
    """Build stable native registration records for the global action set."""
    runtime_virtual_keys(config)
    action_ids = list(RUNTIME_ACTION_IDS)
    if include_quick_run:
        action_ids.extend(QUICK_RUN_ACTION_IDS)
    bindings: list[NativeHotkey] = []
    for index, action_id in enumerate(action_ids, start=1):
        modifiers, vk = _native_key(config.binding_for(action_id))
        bindings.append(
            NativeHotkey(
                action_id=action_id,
                registration_id=index,
                modifiers=modifiers,
                vk=vk,
            )
        )
    return tuple(bindings)


class NativeHotkeySet:
    """Own an all-or-none native registration set."""

    def __init__(self, backend: HotkeyBackend) -> None:
        self._backend = backend
        self._current: tuple[NativeHotkey, ...] = ()

    @property
    def current(self) -> tuple[NativeHotkey, ...]:
        return self._current

    def _register(self, binding: NativeHotkey) -> bool:
        return self._backend.register_hotkey(
            binding.registration_id, binding.modifiers, binding.vk
        )

    def _restore(self, bindings: Sequence[NativeHotkey]) -> bool:
        restored: list[NativeHotkey] = []
        succeeded = True
        for binding in bindings:
            if self._register(binding):
                restored.append(binding)
            else:
                succeeded = False
        self._current = tuple(bindings) if succeeded else tuple(restored)
        return succeeded

    def replace(self, candidate: Sequence[NativeHotkey]) -> RegistrationResult:
        """Replace the complete set, restoring the exact old set on failure."""
        candidate_set = tuple(candidate)
        old_set = self._current
        if candidate_set == old_set:
            return RegistrationResult(success=True)
        removed_old: list[NativeHotkey] = []
        for binding in old_set:
            if self._backend.unregister_hotkey(binding.registration_id):
                removed_old.append(binding)
                continue
            restored_old: list[NativeHotkey] = []
            rollback_succeeded = True
            for removed in removed_old:
                if self._register(removed):
                    restored_old.append(removed)
                else:
                    rollback_succeeded = False
            if rollback_succeeded:
                self._current = old_set
            else:
                restored_ids = {item.registration_id for item in restored_old}
                removed_ids = {item.registration_id for item in removed_old}
                self._current = tuple(
                    item
                    for item in old_set
                    if item.registration_id not in removed_ids
                    or item.registration_id in restored_ids
                )
            return RegistrationResult(
                success=False,
                failed_action_id=binding.action_id,
                failed_key=binding.display_key,
                rollback_succeeded=rollback_succeeded,
            )

        registered_candidate: list[NativeHotkey] = []
        for binding in candidate_set:
            if self._register(binding):
                registered_candidate.append(binding)
                continue
            leaked_candidate = [
                partial
                for partial in registered_candidate
                if not self._backend.unregister_hotkey(partial.registration_id)
            ]
            leaked_ids = {item.registration_id for item in leaked_candidate}
            restored_after_candidate: list[NativeHotkey] = []
            rollback_succeeded = not leaked_candidate
            for old_binding in old_set:
                if old_binding.registration_id in leaked_ids:
                    rollback_succeeded = False
                elif self._register(old_binding):
                    restored_after_candidate.append(old_binding)
                else:
                    rollback_succeeded = False
            self._current = tuple(
                sorted(
                    (*leaked_candidate, *restored_after_candidate),
                    key=lambda item: item.registration_id,
                )
            )
            return RegistrationResult(
                success=False,
                failed_action_id=binding.action_id,
                failed_key=binding.display_key,
                rollback_succeeded=rollback_succeeded,
            )

        self._current = candidate_set
        return RegistrationResult(success=True)


class User32HotkeyBackend:
    """Thin injectable adapter around RegisterHotKey/UnregisterHotKey."""

    def __init__(self, hwnd: int = 0, user32: Any | None = None) -> None:
        if user32 is None:
            if sys.platform != "win32":
                raise OSError("global hotkeys are available only on Windows")
            import ctypes
            import ctypes.wintypes

            user32 = ctypes.windll.user32
            user32.RegisterHotKey.argtypes = [
                ctypes.wintypes.HWND,
                ctypes.c_int,
                ctypes.wintypes.UINT,
                ctypes.wintypes.UINT,
            ]
            user32.RegisterHotKey.restype = ctypes.wintypes.BOOL
            user32.UnregisterHotKey.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
            user32.UnregisterHotKey.restype = ctypes.wintypes.BOOL
        self._hwnd = hwnd
        self._user32 = user32

    def register_hotkey(self, registration_id: int, modifiers: int, vk: int) -> bool:
        return bool(self._user32.RegisterHotKey(self._hwnd, registration_id, modifiers, vk))

    def unregister_hotkey(self, registration_id: int) -> bool:
        return bool(self._user32.UnregisterHotKey(self._hwnd, registration_id))


class UnavailableHotkeyBackend:
    """Non-Windows backend that deterministically selects focused fallbacks."""

    def register_hotkey(self, registration_id: int, modifiers: int, vk: int) -> bool:
        del registration_id, modifiers, vk
        return False

    def unregister_hotkey(self, registration_id: int) -> bool:
        del registration_id
        return True


def registration_id_from_native_message(
    event_type: object,
    message: object,
) -> int | None:
    """Decode a Qt Windows native event without leaking ctypes into the UI layer."""
    if sys.platform != "win32" or event_type not in (
        b"windows_generic_MSG",
        b"windows_dispatcher_MSG",
    ):
        return None
    import ctypes
    import ctypes.wintypes

    msg = ctypes.wintypes.MSG.from_address(int(message))
    return int(msg.wParam) if msg.message == WM_HOTKEY else None
