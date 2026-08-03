from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from macroflow.hotkey_config import (
    DEFAULT_HOTKEY_CONFIG,
    EDITOR_ACTION_IDS,
    QUICK_RUN_ACTION_IDS,
    RUNTIME_ACTION_IDS,
    HotkeyConfig,
)
from macroflow.ui.hotkey_runtime import HotkeyRuntime
from macroflow.win32.hotkeys import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    NativeHotkey,
    NativeHotkeySet,
    RegistrationResult,
    native_hotkeys,
)


class FakeBackend:
    def __init__(
        self,
        fail_ids: set[int] | None = None,
        fail_unregister_ids: set[int] | None = None,
    ) -> None:
        self.fail_ids = set(fail_ids or ())
        self.fail_unregister_ids = set(fail_unregister_ids or ())
        self.calls: list[tuple[object, ...]] = []
        self.registered: dict[int, tuple[int, int]] = {}

    def register_hotkey(self, registration_id: int, modifiers: int, vk: int) -> bool:
        self.calls.append(("register", registration_id, modifiers, vk))
        if registration_id in self.fail_ids:
            self.fail_ids.remove(registration_id)
            return False
        self.registered[registration_id] = (modifiers, vk)
        return True

    def unregister_hotkey(self, registration_id: int) -> bool:
        self.calls.append(("unregister", registration_id))
        if registration_id in self.fail_unregister_ids:
            self.fail_unregister_ids.remove(registration_id)
            return False
        self.registered.pop(registration_id, None)
        return True


class FakeFallbacks:
    def __init__(self) -> None:
        self.bindings: dict[str, str] = {}
        self.callback: Callable[[str], None] | None = None
        self.replacements = 0

    def replace(self, bindings: Mapping[str, str], callback: Callable[[str], None]) -> None:
        self.bindings = dict(bindings)
        self.callback = callback
        self.replacements += 1

    def trigger(self, action_id: str) -> None:
        assert self.callback is not None
        self.callback(action_id)

    def clear(self) -> None:
        self.bindings.clear()
        self.callback = None


def _runtime_config(**runtime_changes: str) -> HotkeyConfig:
    return DEFAULT_HOTKEY_CONFIG.with_bindings(runtime_changes)


def test_native_bindings_are_stable_and_include_mod_norepeat() -> None:
    bindings = native_hotkeys(DEFAULT_HOTKEY_CONFIG)

    assert [(binding.registration_id, binding.action_id, binding.vk) for binding in bindings[:4]] == [
        (1, "runtime.record_or_capture", 0x75),
        (2, "runtime.play_or_color_capture", 0x76),
        (3, "runtime.pause_or_resume", 0x77),
        (4, "recording.quick_text", 0x78),
    ]
    assert all(binding.modifiers == MOD_NOREPEAT for binding in bindings[:4])
    assert [binding.vk for binding in bindings[4:]] == [0x31, 0x32, 0x33, 0x34, 0x35]
    assert all(
        binding.modifiers == MOD_NOREPEAT | MOD_CONTROL | MOD_ALT
        for binding in bindings[4:]
    )


def test_transactional_replace_registers_the_complete_candidate() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    candidate = native_hotkeys(DEFAULT_HOTKEY_CONFIG)

    result = registrar.replace(candidate)

    assert result.success
    assert registrar.current == candidate
    assert backend.registered == {
        binding.registration_id: (binding.modifiers, binding.vk) for binding in candidate
    }


def test_failed_replace_removes_partial_candidate_and_restores_exact_old_set() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    old = native_hotkeys(DEFAULT_HOTKEY_CONFIG)
    assert registrar.replace(old).success
    backend.calls.clear()

    candidate = native_hotkeys(_runtime_config(**{"runtime.record_or_capture": "F10"}))
    backend.fail_ids.add(3)
    result = registrar.replace(candidate)

    assert not result.success
    assert result.failed_action_id == "runtime.pause_or_resume"
    assert result.failed_key == "F8"
    assert result.rollback_succeeded
    assert registrar.current == old
    assert backend.registered == {
        binding.registration_id: (binding.modifiers, binding.vk) for binding in old
    }
    failed_index = backend.calls.index(("register", 3, MOD_NOREPEAT, 0x77))
    assert ("unregister", 1) in backend.calls[failed_index + 1 :]
    assert ("unregister", 2) in backend.calls[failed_index + 1 :]
    assert backend.calls[-len(old):] == [
        ("register", binding.registration_id, binding.modifiers, binding.vk) for binding in old
    ]


def test_failed_candidate_cleanup_tracks_ghost_and_reports_incomplete_rollback() -> None:
    backend = FakeBackend(fail_ids={2}, fail_unregister_ids={1})
    registrar = NativeHotkeySet(backend)
    candidate = native_hotkeys(DEFAULT_HOTKEY_CONFIG)

    result = registrar.replace(candidate)

    assert not result.success
    assert not result.rollback_succeeded
    assert registrar.current == (candidate[0],)
    assert backend.registered == {
        candidate[0].registration_id: (candidate[0].modifiers, candidate[0].vk)
    }

    assert registrar.replace(()).success
    assert registrar.current == ()
    assert backend.registered == {}


def test_identical_native_set_is_a_noop() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    bindings = native_hotkeys(DEFAULT_HOTKEY_CONFIG)
    assert registrar.replace(bindings).success
    backend.calls.clear()

    assert registrar.replace(bindings).success

    assert backend.calls == []


def test_failed_old_set_unregistration_reports_an_incomplete_rollback() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    old = native_hotkeys(DEFAULT_HOTKEY_CONFIG)
    assert registrar.replace(old).success
    backend.fail_unregister_ids.add(2)
    backend.fail_ids.add(1)

    result = registrar.replace(
        native_hotkeys(_runtime_config(**{"runtime.record_or_capture": "F10"}))
    )

    assert not result.success
    assert not result.rollback_succeeded
    assert registrar.current == old[1:]


def test_initialization_attempts_native_registration_only_once() -> None:
    backend = FakeBackend(fail_ids={2})
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    dispatched: list[str] = []
    runtime = HotkeyRuntime(registrar, fallbacks, dispatched.append)

    first = runtime.initialize(DEFAULT_HOTKEY_CONFIG)
    call_count = len(backend.calls)
    second = runtime.initialize(DEFAULT_HOTKEY_CONFIG)

    assert not first.success
    assert second == first
    assert runtime.initialized
    assert not runtime.globally_registered
    assert len(backend.calls) == call_count
    assert fallbacks.bindings == dict(DEFAULT_HOTKEY_CONFIG.bindings)
    assert fallbacks.replacements == 1


def test_optional_quick_run_collision_preserves_global_runtime_controls() -> None:
    backend = FakeBackend(fail_ids={5})
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    runtime = HotkeyRuntime(registrar, fallbacks, lambda _action: None)

    result = runtime.initialize(DEFAULT_HOTKEY_CONFIG)

    assert result.success
    assert result.failed_action_id == "quick_run.slot_1"
    assert runtime.globally_registered
    assert not runtime.quick_run_globally_registered
    assert [binding.action_id for binding in registrar.current] == list(RUNTIME_ACTION_IDS)
    assert set(fallbacks.bindings) == set((*EDITOR_ACTION_IDS, *QUICK_RUN_ACTION_IDS))


def test_incomplete_initial_cleanup_enters_degraded_mode_without_focused_duplicates() -> None:
    backend = FakeBackend(fail_ids={2}, fail_unregister_ids={1})
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    dispatched: list[str] = []
    runtime = HotkeyRuntime(registrar, fallbacks, dispatched.append)

    result = runtime.initialize(DEFAULT_HOTKEY_CONFIG)

    assert not result.success
    assert not result.rollback_succeeded
    assert runtime.degraded
    assert fallbacks.bindings == {}
    assert not runtime.dispatch_native(1)
    assert runtime.shutdown().success
    assert backend.registered == {}


def test_successful_apply_replaces_native_and_focused_bindings_together() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    dispatched: list[str] = []
    runtime = HotkeyRuntime(registrar, fallbacks, dispatched.append)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success
    candidate = DEFAULT_HOTKEY_CONFIG.with_bindings(
        {
            "runtime.record_or_capture": "F10",
            "editor.insert_text": "Alt+T",
        }
    )

    result = runtime.apply(candidate)

    assert result.success
    assert runtime.globally_registered
    assert runtime.config == candidate
    assert runtime.active_runtime_vks == frozenset({0x79, 0x76, 0x77, 0x78})
    assert fallbacks.bindings == {
        "editor.insert_text": "Alt+T",
        "editor.insert_click": "Ctrl+Shift+L",
        "editor.insert_color_trigger": "Ctrl+Shift+G",
    }


def test_editor_only_apply_does_not_release_native_hotkeys() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    runtime = HotkeyRuntime(registrar, fallbacks, lambda _action: None)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success
    backend.calls.clear()
    candidate = DEFAULT_HOTKEY_CONFIG.with_bindings(
        {"editor.insert_text": "Alt+T"}
    )

    assert runtime.apply(candidate).success

    assert backend.calls == []
    assert runtime.config == candidate
    assert fallbacks.bindings["editor.insert_text"] == "Alt+T"


def test_failed_shutdown_retains_ownership_for_retry() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    runtime = HotkeyRuntime(registrar, FakeFallbacks(), lambda _action: None)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success
    backend.fail_unregister_ids.add(2)

    first = runtime.shutdown()

    assert not first.success
    assert runtime.initialized
    assert runtime.degraded
    assert registrar.current
    assert runtime.shutdown().success
    assert not runtime.initialized
    assert registrar.current == ()


def test_failed_apply_keeps_old_config_and_focused_bindings() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    runtime = HotkeyRuntime(registrar, fallbacks, lambda _action: None)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success
    backend.fail_ids.add(1)
    candidate = _runtime_config(**{"runtime.record_or_capture": "F10"})

    result = runtime.apply(candidate)

    assert not result.success
    assert result.failed_action_id == "runtime.record_or_capture"
    assert result.failed_key == "F10"
    assert runtime.config == DEFAULT_HOTKEY_CONFIG
    assert runtime.globally_registered
    assert fallbacks.bindings == {
        action: DEFAULT_HOTKEY_CONFIG.binding_for(action)
        for action in (
            "editor.insert_text",
            "editor.insert_click",
            "editor.insert_color_trigger",
        )
    }
    assert fallbacks.replacements == 1


def test_native_and_focused_paths_dispatch_logical_actions() -> None:
    backend = FakeBackend(fail_ids={1})
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    dispatched: list[str] = []
    runtime = HotkeyRuntime(registrar, fallbacks, dispatched.append)
    assert not runtime.initialize(DEFAULT_HOTKEY_CONFIG).success

    assert not runtime.dispatch_native(2)
    fallbacks.trigger("runtime.play_or_color_capture")
    assert not runtime.dispatch_native(999)

    assert dispatched == ["runtime.play_or_color_capture"]


def test_successful_native_initialization_keeps_only_editor_focused_shortcuts() -> None:
    backend = FakeBackend()
    fallbacks = FakeFallbacks()
    runtime = HotkeyRuntime(NativeHotkeySet(backend), fallbacks, lambda _action: None)

    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success

    assert fallbacks.bindings == {
        action: DEFAULT_HOTKEY_CONFIG.binding_for(action)
        for action in (
            "editor.insert_text",
            "editor.insert_click",
            "editor.insert_color_trigger",
        )
    }


def test_shutdown_unregisters_native_set_and_clears_fallbacks() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    runtime = HotkeyRuntime(registrar, fallbacks, lambda _action: None)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success

    runtime.shutdown()

    assert registrar.current == ()
    assert backend.registered == {}
    assert fallbacks.bindings == {}
    assert not runtime.initialized
    assert not runtime.globally_registered


def test_runtime_accepts_a_registrar_protocol_not_real_user32() -> None:
    class Registrar:
        current: Sequence[NativeHotkey] = ()

        def replace(self, candidate: Sequence[NativeHotkey]) -> RegistrationResult:
            self.current = tuple(candidate)
            return RegistrationResult(success=True)

    registrar = Registrar()
    runtime = HotkeyRuntime(registrar, FakeFallbacks(), lambda _action: None)

    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success
    assert len(registrar.current) == 9


def test_quick_run_hotkeys_can_be_suspended_during_recording_and_restored() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    runtime = HotkeyRuntime(registrar, FakeFallbacks(), lambda _action: None)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success

    suspended = runtime.set_quick_run_enabled(False)

    assert suspended.success
    assert [item.action_id for item in registrar.current] == list(RUNTIME_ACTION_IDS)

    restored = runtime.set_quick_run_enabled(True)

    assert restored.success
    assert len(registrar.current) == 9


def test_incomplete_rollback_marks_runtime_degraded_and_blocks_partial_native_dispatch() -> None:
    backend = FakeBackend()
    registrar = NativeHotkeySet(backend)
    fallbacks = FakeFallbacks()
    dispatched: list[str] = []
    runtime = HotkeyRuntime(registrar, fallbacks, dispatched.append)
    assert runtime.initialize(DEFAULT_HOTKEY_CONFIG).success

    # Candidate id=2 fails, then restoring old id=3 also fails.
    backend.fail_ids.update({2, 3})
    candidate = _runtime_config(
        **{
            "runtime.record_or_capture": "F10",
            "runtime.play_or_color_capture": "F11",
        }
    )

    result = runtime.apply(candidate)

    assert not result.success
    assert not result.rollback_succeeded
    assert runtime.degraded
    assert not runtime.globally_registered
    assert not runtime.dispatch_native(1)
    assert fallbacks.bindings == {}
