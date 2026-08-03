"""UI-facing hotkey runtime orchestration without Qt or user32 coupling."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol

from macroflow.hotkey_config import (
    EDITOR_ACTION_IDS,
    QUICK_RUN_ACTION_IDS,
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
        self._quick_run_enabled = True
        self.initialized = False
        self.globally_registered = False
        self.quick_run_globally_registered = False
        self.degraded = False

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
        include_quick_run: bool = False,
    ) -> dict[str, str]:
        actions: Mapping[str, str] | tuple[str, ...]
        if include_runtime:
            actions = config.bindings
        elif include_quick_run:
            actions = (*EDITOR_ACTION_IDS, *QUICK_RUN_ACTION_IDS)
        else:
            actions = EDITOR_ACTION_IDS
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

        runtime_result = self._registrar.replace(
            native_hotkeys(config, include_quick_run=False)
        )
        result = runtime_result
        quick_run_registered = False
        if runtime_result.success:
            quick_result = self._registrar.replace(
                native_hotkeys(config, include_quick_run=True)
            )
            if quick_result.success:
                result = quick_result
                quick_run_registered = True
            elif quick_result.rollback_succeeded:
                result = RegistrationResult(
                    success=True,
                    failed_action_id=quick_result.failed_action_id,
                    failed_key=quick_result.failed_key,
                    rollback_succeeded=True,
                )
            else:
                result = quick_result
        self._config = config
        self._focused_bindings.replace(
            self._focused_map(
                config,
                include_runtime=not runtime_result.success,
                include_quick_run=runtime_result.success and not quick_run_registered,
            ),
            self.dispatch_focused,
        )
        self._initial_result = result
        self.initialized = True
        self.globally_registered = runtime_result.success
        self.quick_run_globally_registered = quick_run_registered
        self.degraded = not result.rollback_succeeded
        self._refresh_native_actions()
        if self.degraded:
            self._focused_bindings.clear()
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
        result = self._registrar.replace(
            native_hotkeys(candidate, include_quick_run=self._quick_run_enabled)
        )
        if not result.success:
            self.degraded = not result.rollback_succeeded
            self.globally_registered = (
                was_globally_registered and result.rollback_succeeded
            )
            if self.degraded:
                self._focused_bindings.clear()
                self._native_actions.clear()
            else:
                self._refresh_native_actions()
            return result

        self._focused_bindings.replace(
            self._focused_map(candidate, include_runtime=False),
            self.dispatch_focused,
        )
        self._config = candidate
        self.globally_registered = True
        self.quick_run_globally_registered = self._quick_run_enabled
        self.degraded = False
        self._refresh_native_actions()
        return result

    def set_quick_run_enabled(self, enabled: bool) -> RegistrationResult:
        """Atomically suspend or restore quick-run globals around recording."""
        if not self.initialized:
            raise RuntimeError("hotkey runtime is not initialized")
        if enabled == self._quick_run_enabled:
            return RegistrationResult(success=True)
        result = self._registrar.replace(
            native_hotkeys(self.config, include_quick_run=enabled)
        )
        if not result.success:
            self.degraded = not result.rollback_succeeded
            if self.degraded:
                self._native_actions.clear()
            else:
                self._refresh_native_actions()
                self.quick_run_globally_registered = any(
                    binding.action_id in QUICK_RUN_ACTION_IDS
                    for binding in self._registrar.current
                )
                self._focused_bindings.replace(
                    self._focused_map(
                        self.config,
                        include_runtime=False,
                        include_quick_run=(
                            enabled and not self.quick_run_globally_registered
                        ),
                    ),
                    self.dispatch_focused,
                )
            return result
        self._quick_run_enabled = enabled
        self.quick_run_globally_registered = enabled
        self.degraded = False
        self._refresh_native_actions()
        self._focused_bindings.replace(
            self._focused_map(self.config, include_runtime=False),
            self.dispatch_focused,
        )
        return result

    def dispatch_native(self, registration_id: int) -> bool:
        """Dispatch an incoming WM_HOTKEY registration id exactly once."""
        if self.degraded:
            return False
        action_id = self._native_actions.get(registration_id)
        if action_id is None:
            return False
        self._dispatch(action_id)
        return True

    def dispatch_focused(self, action_id: str) -> None:
        """Dispatch a logical action from the focused QShortcut path."""
        if self.degraded:
            return
        if self._config is None or action_id not in self._config.bindings:
            raise KeyError(action_id)
        self._dispatch(action_id)

    def shutdown(self) -> RegistrationResult:
        """Release every owned shortcut; retain ownership state when release fails."""
        result = self._registrar.replace(())
        self._focused_bindings.clear()
        self._native_actions.clear()
        if not result.success:
            self.globally_registered = False
            self.quick_run_globally_registered = False
            self.degraded = True
            return result
        self.initialized = False
        self.globally_registered = False
        self.quick_run_globally_registered = False
        self.degraded = False
        self._config = None
        self._quick_run_enabled = True
        self._initial_result = None
        return result
