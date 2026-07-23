"""End-to-end regressions discovered by the 2026-07 functional audit."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

from macroflow import player
from macroflow.script_engine import ColorCheckNode, FlowEngine
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
)


def _run_offscreen(script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        env=env,
    )


def _macro(events: list[object], settings: MacroSettings | None = None) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="test",
            created_at="2026-07-13T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=settings or MacroSettings(),
        raw_events=[],
        events=events,  # type: ignore[arg-type]
    )


def test_overlay_expands_for_max_repeat_without_clipping() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtGui import QFont, QFontMetrics
        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.overlay import OverlayWindow

        app = QApplication.instance() or QApplication([])
        overlay = OverlayWindow()
        overlay.start_playing(5.0, repeat_current=9999, repeat_total=9999)
        overlay.set_progress(1.0)
        app.processEvents()

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        text = "PLAY  9999/9999회  100%  5.0x"
        required_width = 36 + QFontMetrics(font).horizontalAdvance(text) + 12
        assert overlay.width() >= required_width
        """
    )

    assert result.returncode == 0, result.stderr


def test_flow_overlay_lifecycle_and_sequencer_progress_signal() -> None:
    result = _run_offscreen(
        """
        import tempfile
        from pathlib import Path

        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / "one.json", Path(directory) / "two.json"]
            for path in paths:
                path.write_text("{}", encoding="utf-8")

            window = MainWindow()
            for path in paths:
                window._sequencer.add_macro_file(path)

            progress = []
            window._sequencer.sequence_progress.connect(
                lambda current, total: progress.append((current, total))
            )
            window._sequencer.run_sequence = lambda speed=1.0: None
            window._toggle_sequencer()
            app.processEvents()

            assert window._overlay.isVisible()
            assert window._overlay._mode == "flowing"
            assert window._overlay._flow_total == 2

            window._sequencer._active_generation = 1
            window._sequencer._apply_node_start(1, "macro_001", "two.json")
            app.processEvents()
            assert progress == [(2, 2)]
            assert window._overlay._flow_current == 2

            window._on_sequence_done("success")
            app.processEvents()
            assert not window._overlay.isVisible()
        """
    )

    assert result.returncode == 0, result.stderr


def test_player_start_failure_restores_idle_overlay_state() -> None:
    result = _run_offscreen(
        """
        import time
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow import player
        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.playback_repeat import range_playback_options

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window._macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="test", created_at="2026-07-13T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(),
            raw_events=[],
            events=[WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=1)],
        )

        with patch.object(player, "play", side_effect=player.PlaybackError("busy")), \\
             patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok):
            window._start_playback(options=range_playback_options((0, 1)))
            deadline = time.monotonic() + 1.0
            while window._state != "idle" and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)

        assert window._state == "idle"
        assert not window._overlay.isVisible()
        """
    )

    assert result.returncode == 0, result.stderr


def test_repeat_confirmation_brings_main_window_to_front_first() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow import win32
        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window._macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="test", created_at="2026-07-23T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(),
            raw_events=[],
            events=[WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=1)],
        )
        window._repeat_spin.setValue(2)

        calls = []
        with patch.object(window, "isMinimized", return_value=False), \\
             patch.object(window, "show", side_effect=lambda: calls.append("show")), \\
             patch.object(window, "raise_", side_effect=lambda: calls.append("raise")), \\
             patch.object(window, "activateWindow", side_effect=lambda: calls.append("activate")), \\
             patch("macroflow.ui.main_window.sys.platform", "win32"), \\
             patch.object(
                 win32,
                 "bring_window_to_foreground",
                 side_effect=lambda hwnd: calls.append(("native", hwnd)) or True,
             ), \\
             patch.object(
                 QMessageBox,
                 "question",
                 side_effect=lambda *args, **kwargs: (
                     calls.append("question") or QMessageBox.StandardButton.No
                 ),
             ):
            window._start_playback()

        assert calls == [
            "show",
            "raise",
            "activate",
            ("native", int(window.winId())),
            "question",
        ]
        assert window._state == "idle"
        """
    )

    assert result.returncode == 0, result.stderr


def test_flow_color_check_timeout_zero_waits_until_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import win32

    calls = 0
    done_calls: list[tuple[str, bool, str]] = []

    def get_pixel(_x: int, _y: int) -> tuple[int, int, int]:
        nonlocal calls
        calls += 1
        return (255, 255, 255) if calls >= 3 else (0, 0, 0)

    monkeypatch.setattr(win32, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(win32, "get_pixel_color", get_pixel)
    engine = FlowEngine(
        str(tmp_path / "sequence.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
    )
    node = ColorCheckNode(
        id="color_000",
        label="color",
        x_ratio=0.0,
        y_ratio=0.0,
        target_color="#FFFFFF",
        timeout_ms=0,
        check_interval_ms=1,
        on_match="matched",
        on_timeout="timed_out",
    )

    assert engine._run_color_check_node(node) == "matched"
    assert calls == 3
    assert done_calls == [("color_000", True, "색 감지 성공")]


@pytest.mark.parametrize("interval_ms", [0, -10])
def test_flow_color_check_clamps_non_positive_poll_interval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interval_ms: int,
) -> None:
    from macroflow import win32

    calls = 0
    waits: list[float] = []

    class StopFlag:
        def is_set(self) -> bool:
            return False

        def wait(self, seconds: float) -> bool:
            waits.append(seconds)
            return False

    def get_pixel(_x: int, _y: int) -> tuple[int, int, int]:
        nonlocal calls
        calls += 1
        return (255, 255, 255) if calls >= 2 else (0, 0, 0)

    monkeypatch.setattr(win32, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(win32, "get_pixel_color", get_pixel)
    engine = FlowEngine(str(tmp_path / "sequence.macroflow"))
    engine._stop_flag = StopFlag()  # type: ignore[assignment]
    node = ColorCheckNode(
        id="color_000",
        label="color",
        x_ratio=0.0,
        y_ratio=0.0,
        target_color="#FFFFFF",
        timeout_ms=1000,
        check_interval_ms=interval_ms,
        on_match="matched",
        on_timeout="timed_out",
    )

    assert engine._run_color_check_node(node) == "matched"
    assert waits == [0.001]


def test_macro_color_trigger_clamps_non_positive_poll_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    waits: list[float] = []
    calls = 0

    class StopFlag:
        def is_set(self) -> bool:
            return False

        def wait(self, seconds: float) -> bool:
            waits.append(seconds)
            return False

    def get_pixel(_x: int, _y: int) -> tuple[int, int, int]:
        nonlocal calls
        calls += 1
        return (0, 255, 0) if calls >= 2 else (0, 0, 0)

    monkeypatch.setattr(player, "_stop_flag", StopFlag())
    monkeypatch.setattr(player, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(player, "send_mouse_move", lambda _x, _y: None)
    monkeypatch.setattr(player, "get_pixel_color", get_pixel)
    event = ColorTriggerEvent(
        id="color",
        type="color_trigger",
        timestamp_ns=0,
        x_ratio=0.0,
        y_ratio=0.0,
        target_color="#00FF00",
        timeout_ms=0,
        check_interval_ms=0,
    )

    player._wait_for_color(event)

    assert waits == [0.05, 0.001]


def test_delay_override_shifts_following_timestamp_and_preserves_click(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = threading.Event()
    event_times: list[float] = []
    buttons: list[tuple[bool, str]] = []
    drags: list[tuple[int, ...]] = []
    monkeypatch.setattr(player, "ratio_to_pixel", lambda x, y: (int(x), int(y)))
    monkeypatch.setattr(player, "send_mouse_move", lambda _x, _y: None)
    monkeypatch.setattr(
        player,
        "send_mouse_button",
        lambda _x, _y, button, *, down: buttons.append((down, button)),
    )
    monkeypatch.setattr(player, "send_mouse_drag", lambda *args: drags.append(args))
    events = [
        MouseMoveEvent(
            id="base", type="mouse_move", timestamp_ns=0, x_ratio=1.0, y_ratio=1.0
        ),
        MouseButtonEvent(
            id="down",
            type="mouse_down",
            timestamp_ns=100_000_000,
            delay_override_ms=20,
            x_ratio=2.0,
            y_ratio=2.0,
            button="left",
        ),
        MouseButtonEvent(
            id="up",
            type="mouse_up",
            timestamp_ns=130_000_000,
            x_ratio=2.0,
            y_ratio=2.0,
            button="left",
        ),
    ]

    player.play(
        _macro(events, MacroSettings(click_time_threshold_ms=70)),
        on_event=lambda _idx, _event: event_times.append(time.perf_counter()),
        on_complete=completed.set,
    )
    assert completed.wait(timeout=1.0)

    assert len(event_times) == 3
    assert 0.005 <= event_times[1] - event_times[0] <= 0.08
    assert 0.01 <= event_times[2] - event_times[1] <= 0.07
    assert buttons == [(True, "left"), (False, "left")]
    assert drags == []


def test_recorded_relative_time_does_not_mix_in_playback_override() -> None:
    from macroflow.ui.editor_rows import _build_rows

    events = [
        MouseButtonEvent(
            id="a", type="mouse_down", timestamp_ns=100_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
        ),
        MouseButtonEvent(
            id="b", type="mouse_up", timestamp_ns=120_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
        ),
        MouseButtonEvent(
            id="c", type="mouse_down", timestamp_ns=999_000_000,
            delay_override_ms=500, x_ratio=0.5, y_ratio=0.5, button="left",
        ),
        MouseButtonEvent(
            id="d", type="mouse_up", timestamp_ns=1_020_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
        ),
    ]

    rows = _build_rows(events, show_moves=False)

    assert rows[1].time_ms_rel == pytest.approx(899.0)
    assert rows[1].delay_str == "500"


def test_delay_input_semantics_are_explicit() -> None:
    from macroflow.ui.editor_rows import (
        delay_input_to_override,
        delay_override_to_input,
    )

    assert delay_input_to_override(-1) is None
    assert delay_input_to_override(0) == 0
    assert delay_input_to_override(250) == 250
    assert delay_override_to_input(None) == -1
    assert delay_override_to_input(0) == 0


def test_time_headers_name_recorded_time_and_playback_wait() -> None:
    from macroflow.ui.editor_table import COLUMNS

    assert COLUMNS[4] == "기록 시점(ms)"
    assert COLUMNS[5] == "재생 대기(ms)"


def test_external_color_settings_are_normalized_at_load_boundary() -> None:
    from macroflow.macro_file import _dict_to_event, _dict_to_settings

    settings = _dict_to_settings(
        {
            "color_check_click_wait_timeout_ms": -1,
            "color_check_click_skip_timeout_ms": 999999,
            "color_check_click_interval_ms": 0,
            "color_trigger_default_timeout_ms": "bad",
            "color_trigger_check_interval_ms": -10,
        }
    )
    event = _dict_to_event(
        {
            "id": "color",
            "type": "color_trigger",
            "timestamp_ns": 0,
            "x_ratio": 0.0,
            "y_ratio": 0.0,
            "target_color": "#FFFFFF",
            "timeout_ms": -100,
            "check_interval_ms": 0,
        }
    )

    assert settings.color_check_click_wait_timeout_ms == 0
    assert settings.color_check_click_skip_timeout_ms == 600000
    assert settings.color_check_click_interval_ms == 1
    assert settings.color_trigger_default_timeout_ms == 0
    assert settings.color_trigger_check_interval_ms == 1
    assert isinstance(event, ColorTriggerEvent)
    assert event.timeout_ms == 0
    assert event.check_interval_ms == 1


def test_regular_operations_are_blocked_while_sequence_runs() -> None:
    result = _run_offscreen(
        """
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from macroflow.ui.main_window import MainWindow

        status = SimpleNamespace(setText=MagicMock())
        sequence = SimpleNamespace(is_running=lambda: True)
        recording_host = SimpleNamespace(
            _sequencer=sequence,
            _state="idle",
            _start_recording=MagicMock(),
            _sb_state=status,
        )
        MainWindow._toggle_recording(recording_host)
        recording_host._start_recording.assert_not_called()

        playback_host = SimpleNamespace(
            _sequencer=sequence,
            _state="idle",
            _macro=object(),
            _is_sequencer_tab=lambda: False,
            _is_favorites_tab=lambda: False,
            _start_playback=MagicMock(),
            _sb_state=status,
        )
        MainWindow._toggle_playback(playback_host)
        playback_host._start_playback.assert_not_called()
        """
    )

    assert result.returncode == 0, result.stderr


def test_sequence_start_is_blocked_while_regular_operation_runs() -> None:
    result = _run_offscreen(
        """
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from macroflow.ui.main_window import MainWindow

        sequence = SimpleNamespace(
            is_running=lambda: False,
            has_items=lambda: True,
            run_sequence=MagicMock(),
        )
        host = SimpleNamespace(
            _sequencer=sequence,
            _state="playing",
            _sb_state=SimpleNamespace(setText=MagicMock()),
        )
        MainWindow._toggle_sequencer(host)
        sequence.run_sequence.assert_not_called()
        """
    )

    assert result.returncode == 0, result.stderr


def test_stop_during_color_read_prevents_mouse_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered_read = threading.Event()
    release_read = threading.Event()
    buttons: list[tuple[bool, str]] = []
    player._stop_flag.clear()

    def blocking_pixel(_x: int, _y: int) -> tuple[int, int, int]:
        entered_read.set()
        assert release_read.wait(timeout=1.0)
        return (255, 0, 0)

    monkeypatch.setattr(player, "ratio_to_pixel", lambda _x, _y: (10, 20))
    monkeypatch.setattr(player, "get_pixel_color", blocking_pixel)
    monkeypatch.setattr(player, "send_mouse_move", lambda _x, _y: None)
    monkeypatch.setattr(
        player,
        "send_mouse_button",
        lambda _x, _y, button, *, down: buttons.append((down, button)),
    )
    event = MouseButtonEvent(
        id="down",
        type="mouse_down",
        timestamp_ns=0,
        x_ratio=0.5,
        y_ratio=0.5,
        button="left",
        recorded_color="#FF0000",
        color_check_enabled=True,
        color_check_on_mismatch="skip",
    )
    worker = threading.Thread(
        target=player._execute_event,
        args=(event, MacroSettings(color_check_click_skip_timeout_ms=0), player._PlayState()),
    )
    worker.start()
    assert entered_read.wait(timeout=1.0)
    player._stop_flag.set()
    release_read.set()
    worker.join(timeout=1.0)
    player._stop_flag.clear()

    assert not worker.is_alive()
    assert buttons == []


def test_click_color_timeout_does_not_overshoot_poll_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    player._stop_flag.clear()
    monkeypatch.setattr(player, "get_pixel_color", lambda _x, _y: (0, 0, 0))
    started = time.perf_counter()
    matched = player._wait_for_click_color_check(
        0,
        0,
        (255, 255, 255),
        MacroSettings(
            color_check_click_skip_timeout_ms=10,
            color_check_click_interval_ms=200,
        ),
        "skip",
    )
    elapsed = time.perf_counter() - started

    assert matched is False
    assert elapsed < 0.1


def test_flow_color_timeout_rejects_match_after_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import win32

    calls = 0

    def get_pixel(_x: int, _y: int) -> tuple[int, int, int]:
        nonlocal calls
        calls += 1
        return (255, 255, 255) if calls >= 2 else (0, 0, 0)

    monkeypatch.setattr(win32, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(win32, "get_pixel_color", get_pixel)
    engine = FlowEngine(str(tmp_path / "sequence.macroflow"))
    node = ColorCheckNode(
        id="color",
        label="color",
        x_ratio=0.0,
        y_ratio=0.0,
        target_color="#FFFFFF",
        timeout_ms=10,
        check_interval_ms=200,
        on_match="matched",
        on_timeout="timed_out",
    )
    started = time.perf_counter()
    result = engine._run_color_check_node(node)
    elapsed = time.perf_counter() - started

    assert result == "timed_out"
    assert calls == 1
    assert elapsed < 0.1


def test_loop_nested_delay_override_uses_scheduler_and_speed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow.types import KeyEvent, LoopEvent

    key_times: list[float] = []
    player._stop_flag.clear()
    monkeypatch.setattr(
        player,
        "send_key",
        lambda _vk, *, is_down: key_times.append(time.perf_counter()),
    )
    nested: list[AnyEvent] = [
        KeyEvent(id="down", type="key_down", timestamp_ns=0, key="a", vk_code=65),
        KeyEvent(
            id="up",
            type="key_up",
            timestamp_ns=0,
            delay_override_ms=120,
            key="a",
            vk_code=65,
        ),
    ]
    loop = LoopEvent(
        id="loop",
        type="loop",
        timestamp_ns=0,
        count=1,
        events=nested,
    )

    player._execute_event(loop, MacroSettings(), player._PlayState(speed=2.0))

    assert len(key_times) == 2
    assert 0.04 <= key_times[1] - key_times[0] <= 0.15


def test_condition_elapsed_time_preserves_following_recorded_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow.types import ConditionEvent, KeyEvent, WaitEvent

    key_times: list[float] = []
    player._stop_flag.clear()
    monkeypatch.setattr(
        player,
        "send_key",
        lambda _vk, *, is_down: key_times.append(time.perf_counter()),
    )
    condition = ConditionEvent(
        id="condition",
        type="condition",
        timestamp_ns=0,
        expression="True",
        if_true=[
            WaitEvent(
                id="inner-wait",
                type="wait",
                timestamp_ns=0,
                duration_ms=200,
            )
        ],
    )
    key = KeyEvent(
        id="key",
        type="key_down",
        timestamp_ns=200_000_000,
        key="a",
        vk_code=65,
    )
    started = time.perf_counter()

    player._play_loop(_macro([condition, key]), 2.0, None, None, None, None)

    assert len(key_times) == 1
    assert 0.17 <= key_times[0] - started <= 0.35


def test_emergency_hook_failure_keeps_playback_idle() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow import win32
        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.playback_repeat import range_playback_options

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        window._macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="test", created_at="2026-07-14T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(),
            raw_events=[],
            events=[WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=1)],
        )
        with patch.object(win32, "start_emergency_hook", side_effect=RuntimeError("hook failed")), \
             patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok):
            window._start_playback(options=range_playback_options((0, 1)))

        assert window._state == "idle"
        assert not window._overlay.isVisible()
        assert not window._poll_timer.isActive()
        """
    )

    assert result.returncode == 0, result.stderr


def test_sequencer_generation_stop_timeout_and_mutation_guards() -> None:
    result = _run_offscreen(
        """
        import tempfile
        from pathlib import Path

        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.sequencer import MacroSequencerWidget

        class StillRunningEngine:
            def __init__(self):
                self.stop_calls = 0

            def stop(self):
                self.stop_calls += 1

            def is_running(self):
                return True

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            first.write_text("{}", encoding="utf-8")
            second.write_text("{}", encoding="utf-8")
            widget = MacroSequencerWidget()
            widget.add_macro_file(first)
            engine = StillRunningEngine()
            widget._engine = engine
            widget._active_generation = 2
            widget._run_generation = 2
            widget._update_buttons()

            assert widget.stop_sequence() is False
            assert widget._engine is engine
            assert widget.is_running()
            widget.add_macro_file(second)
            assert widget.item_count() == 1

            widget._list.setCurrentRow(0)
            widget._remove_selected()
            assert widget.item_count() == 1
            widget._apply_node_start(2, "macro_999", "missing")

            widget._apply_sequence_complete(1, "success")
            assert widget._engine is engine
            assert widget._active_generation == 2
        """
    )

    assert result.returncode == 0, result.stderr
