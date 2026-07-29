"""Win32 global-hotkey registration with transactional set replacement."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final, Protocol

from macroflow.hotkey_config import (
    RUNTIME_ACTION_IDS,
    HotkeyConfig,
    runtime_virtual_keys,
)

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
        if 0x70 <= self.vk <= 0x87:
            return f"F{self.vk - 0x70 + 1}"
        return f"VK_{self.vk:02X}"


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


def native_hotkeys(config: HotkeyConfig) -> tuple[NativeHotkey, ...]:
    """Build stable native registration records for the runtime action set."""
    virtual_keys = runtime_virtual_keys(config)
    if len(virtual_keys) != len(RUNTIME_ACTION_IDS):
        raise ValueError("runtime hotkeys must be unique")
    return tuple(
        NativeHotkey(
            action_id=action_id,
            registration_id=index,
            modifiers=MOD_NOREPEAT,
            vk=0x70 + int(config.binding_for(action_id)[1:]) - 1,
        )
        for index, action_id in enumerate(RUNTIME_ACTION_IDS, start=1)
    )


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
            for partial in registered_candidate:
                self._backend.unregister_hotkey(partial.registration_id)
            rollback_succeeded = self._restore(old_set)
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

            user32 = ctypes.windll.user32
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
    if sys.platform != "win32" or event_type != b"windows_generic_MSG":
        return None
    import ctypes
    import ctypes.wintypes

    msg = ctypes.wintypes.MSG.from_address(int(message))
    return int(msg.wParam) if msg.message == WM_HOTKEY else None
