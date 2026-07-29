"""UI-facing hotkey runtime orchestration without Qt or user32 coupling."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol

from macroflow.hotkey_config import (
    EDITOR_ACTION_IDS,
    HotkeyConfig,
    runtime_virtual_keys,
    validate_hotkey_config,
)
from macroflow.win32.hotkeys import (
    HotkeyRegistrar,
    RegistrationResult,
    native_hotkeys,
)


class FocusedHotkeyBindings(Protocol):
    """Adapter implemented by the future QShortcut integration layer."""

    def replace(
        self, bindings: Mapping[str, str], callback: Callable[[str], None]
    ) -> None: ...

    def clear(self) -> None: ...


class HotkeyRuntime:
    """Coordinate native runtime keys, focused fallbacks, and command dispatch."""

    def __init__(
        self,
        registrar: HotkeyRegistrar,
        focused_bindings: FocusedHotkeyBindings,
        dispatch: Callable[[str], None],
    ) -> None:
        self._registrar = registrar
        self._focused_bindings = focused_bindings
        self._dispatch = dispatch
        self._config: HotkeyConfig | None = None
        self._initial_result: RegistrationResult | None = None
        self._native_actions: dict[int, str] = {}
        self.initialized = False
        self.globally_registered = False

    @property
    def config(self) -> HotkeyConfig:
        if self._config is None:
            raise RuntimeError("hotkey runtime is not initialized")
        return self._config

    @property
    def active_runtime_vks(self) -> frozenset[int]:
        return runtime_virtual_keys(self.config)

    @staticmethod
    def _focused_map(
        config: HotkeyConfig,
        *,
        include_runtime: bool,
    ) -> dict[str, str]:
        actions = config.bindings if include_runtime else EDITOR_ACTION_IDS
        return {
            action: config.binding_for(action)
            for action in actions
            if config.binding_for(action)
        }

    def _refresh_native_actions(self) -> None:
        self._native_actions = {
            binding.registration_id: binding.action_id for binding in self._registrar.current
        }

    def initialize(self, config: HotkeyConfig) -> RegistrationResult:
        """Install fallbacks and attempt native registration exactly once."""
        if self.initialized:
            assert self._initial_result is not None
            return self._initial_result
        validation = validate_hotkey_config(config)
        if not validation.is_valid:
            raise ValueError("cannot initialize invalid hotkey config")

        result = self._registrar.replace(native_hotkeys(config))
        self._config = config
        self._focused_bindings.replace(
            self._focused_map(config, include_runtime=not result.success),
            self.dispatch_focused,
        )
        self._initial_result = result
        self.initialized = True
        self.globally_registered = result.success
        self._refresh_native_actions()
        return result

    def apply(self, candidate: HotkeyConfig) -> RegistrationResult:
        """Apply a valid candidate without persisting it.

        Persistence intentionally belongs to the integration layer and should
        happen only after this method returns a successful result.
        """
        if not self.initialized:
            raise RuntimeError("hotkey runtime is not initialized")
        validation = validate_hotkey_config(candidate)
        if not validation.is_valid:
            raise ValueError("cannot apply invalid hotkey config")

        was_globally_registered = self.globally_registered
        result = self._registrar.replace(native_hotkeys(candidate))
        if not result.success:
            self.globally_registered = was_globally_registered and result.rollback_succeeded
            self._refresh_native_actions()
            return result

        self._focused_bindings.replace(
            self._focused_map(candidate, include_runtime=False),
            self.dispatch_focused,
        )
        self._config = candidate
        self.globally_registered = True
        self._refresh_native_actions()
        return result

    def dispatch_native(self, registration_id: int) -> bool:
        """Dispatch a WM_HOTKEY registration ID; return whether it was known."""
        action_id = self._native_actions.get(registration_id)
        if action_id is None:
            return False
        self._dispatch(action_id)
        return True

    def dispatch_focused(self, action_id: str) -> None:
        """Dispatch a logical action from the focused QShortcut path."""
        if self._config is None or action_id not in self._config.bindings:
            raise KeyError(action_id)
        self._dispatch(action_id)

    def shutdown(self) -> RegistrationResult:
        """Release native and focused registrations."""
        result = self._registrar.replace(())
        self._focused_bindings.clear()
        self._native_actions.clear()
        self.initialized = False
        self.globally_registered = False
        self._config = None
        self._initial_result = None
        return result
