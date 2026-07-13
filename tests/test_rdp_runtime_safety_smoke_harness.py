"""Contract tests for the Windows runtime-safety RDP smoke harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from macroflow.types import MouseButtonEvent, WaitEvent

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "rdp_runtime_safety_smoke.py"
_RUNNER = Path(__file__).resolve().parents[1] / "tools" / "run_rdp_runtime_safety_smoke.ps1"


def _load_harness():
    spec = importlib.util.spec_from_file_location("rdp_runtime_safety_smoke", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stop_macro_waits_before_real_click() -> None:
    harness = _load_harness()

    macro = harness.build_stop_macro(
        screen_size=(1800, 1200),
        button_xy=(900, 700),
        wait_ms=5_000,
    )

    assert [event.type for event in macro.events] == ["wait", "mouse_down", "mouse_up"]
    assert isinstance(macro.events[0], WaitEvent)
    assert macro.events[0].duration_ms == 5_000
    assert isinstance(macro.events[1], MouseButtonEvent)
    assert macro.events[1].x_ratio == 0.5
    assert macro.events[1].y_ratio == 700 / 1200


def test_hotkey_assertions_require_fast_stop_without_late_click() -> None:
    harness = _load_harness()

    assertions = harness.evaluate_hotkey_result(
        hotkeys_registered=True,
        playback_started=True,
        playback_stopped=True,
        stop_elapsed_s=0.075,
        target_clicks=0,
        final_state="idle",
    )

    assert all(assertions.values())
    assert (
        harness.evaluate_hotkey_result(
            hotkeys_registered=True,
            playback_started=True,
            playback_stopped=True,
            stop_elapsed_s=0.250,
            target_clicks=0,
            final_state="idle",
        )["stop_under_200ms"]
        is False
    )
    assert (
        harness.evaluate_hotkey_result(
            hotkeys_registered=True,
            playback_started=True,
            playback_stopped=True,
            stop_elapsed_s=0.075,
            target_clicks=1,
            final_state="idle",
        )["no_late_click"]
        is False
    )


def test_sequencer_assertions_require_once_only_gui_thread_updates() -> None:
    harness = _load_harness()

    assertions = harness.evaluate_sequencer_result(
        completed=True,
        item_statuses=["done", "done"],
        list_texts=["✅  first.json", "✅  second.json"],
        started_counts={"macro_000": 1, "macro_001": 1},
        finished_counts={"macro_000": 1, "macro_001": 1},
        gui_thread_updates=[True, True, True, True],
        log_text="실행: first.json\n완료: 완료\n실행: second.json\n완료: 완료",
    )

    assert all(assertions.values())
    duplicate = harness.evaluate_sequencer_result(
        completed=True,
        item_statuses=["done", "done"],
        list_texts=["✅  first.json", "✅  second.json"],
        started_counts={"macro_000": 1, "macro_001": 1},
        finished_counts={"macro_000": 2, "macro_001": 1},
        gui_thread_updates=[True, True],
        log_text="실행: first.json\n완료: 완료\n실행: second.json\n완료: 완료",
    )
    assert duplicate["node_finished_once"] is False


def test_windows_runner_preserves_structured_evidence_contract() -> None:
    script = _RUNNER.read_text(encoding="utf-8")

    assert "Start-Process" in script
    assert "-RedirectStandardOutput" in script
    assert "-RedirectStandardError" in script
    assert "RUNTIME_SAFETY_EXIT=" in script
    assert "RUNTIME_SAFETY_REPORT=" in script
    assert "Get-Content $report -Raw -Encoding utf8" in script
    assert "Set-Clipboard" in script


def test_cli_status_line_is_safe_for_windows_cp949_console() -> None:
    harness = _load_harness()

    line = harness.format_status_line({"ok": True, "list_texts": ["✅  first.json"]})

    line.encode("cp949")
    assert line.startswith("RUNTIME_SAFETY_STATUS=")
    assert "\\u2705" in line
