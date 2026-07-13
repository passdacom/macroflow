"""Windows RDP runtime-safety smoke for MacroFlow hotkeys and Sequencer.

Run this inside the visible Windows RDP checkout. The harness uses the real
Windows global-hotkey path, real player wait cancellation, and a real
FlowEngine worker driving MacroSequencerWidget. Results are written as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import traceback
from collections import Counter
from pathlib import Path
from typing import Any

from macroflow.types import (
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    WaitEvent,
)


def _meta(description: str) -> MacroMeta:
    return MacroMeta(
        version="1.0",
        app_version="rdp-runtime-safety-smoke",
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        screen_width=1920,
        screen_height=1080,
        dpi_scale=1.0,
        description=description,
    )


def build_stop_macro(
    *,
    screen_size: tuple[int, int],
    button_xy: tuple[int, int],
    wait_ms: int = 5_000,
) -> MacroData:
    """Build a long-wait macro whose post-wait click must never run after F7."""
    width, height = screen_size
    x_ratio = button_xy[0] / width
    y_ratio = button_xy[1] / height
    wait_ns = wait_ms * 1_000_000
    events = [
        WaitEvent(
            id="waitstop",
            type="wait",
            timestamp_ns=0,
            duration_ms=wait_ms,
        ),
        MouseButtonEvent(
            id="clickdn1",
            type="mouse_down",
            timestamp_ns=wait_ns + 100_000_000,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            button="left",
        ),
        MouseButtonEvent(
            id="clickup1",
            type="mouse_up",
            timestamp_ns=wait_ns + 180_000_000,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            button="left",
        ),
    ]
    meta = _meta("F7 long-wait cancellation smoke")
    meta.screen_width = width
    meta.screen_height = height
    return MacroData(
        meta=meta,
        settings=MacroSettings(),
        raw_events=events,
        events=events,
    )


def evaluate_hotkey_result(
    *,
    hotkeys_registered: bool,
    playback_started: bool,
    playback_stopped: bool,
    stop_elapsed_s: float | None,
    target_clicks: int,
    final_state: str,
) -> dict[str, bool]:
    """Return the observable contract for the live global-hotkey smoke."""
    return {
        "global_hotkeys_registered": hotkeys_registered,
        "f7_started_playback": playback_started,
        "f7_stopped_playback": playback_stopped,
        "stop_under_200ms": stop_elapsed_s is not None and stop_elapsed_s < 0.2,
        "no_late_click": target_clicks == 0,
        "main_window_idle": final_state == "idle",
    }


def evaluate_sequencer_result(
    *,
    completed: bool,
    item_statuses: list[str],
    list_texts: list[str],
    started_counts: dict[str, int],
    finished_counts: dict[str, int],
    gui_thread_updates: list[bool],
    log_text: str,
) -> dict[str, bool]:
    """Return the observable contract for live worker-to-Qt handoff."""
    macro_nodes = ("macro_000", "macro_001")
    return {
        "sequence_completed": completed,
        "items_done": item_statuses == ["done", "done"],
        "list_rows_done": len(list_texts) == 2
        and all(text.startswith("✅") for text in list_texts),
        "node_started_once": all(started_counts.get(node_id) == 1 for node_id in macro_nodes),
        "node_finished_once": all(finished_counts.get(node_id) == 1 for node_id in macro_nodes),
        "ui_updates_on_gui_thread": bool(gui_thread_updates) and all(gui_thread_updates),
        "execution_log_visible": all(
            token in log_text for token in ("실행: first.json", "실행: second.json", "완료:")
        ),
    }


def _pump_until(app: Any, predicate: Any, timeout_s: float) -> bool:
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    app.processEvents()
    return bool(predicate())


def _press_function_key(vk_code: int) -> None:
    import ctypes

    keyeventf_keyup = 0x0002
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, keyeventf_keyup, 0)


def _run_hotkey_smoke(app: Any, work_dir: Path) -> dict[str, Any]:
    from PyQt6.QtCore import QSettings
    from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

    from macroflow import player
    from macroflow.ui.main_window import MainWindow
    from macroflow.win32 import get_logical_screen_size

    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(work_dir))

    target = QWidget()
    target.setWindowTitle("MacroFlow Runtime Safety Target")
    layout = QVBoxLayout(target)
    button = QPushButton("POST_STOP_CLICK_MUST_NOT_RUN")
    layout.addWidget(button)
    target_clicks = {"count": 0}
    button.clicked.connect(lambda: target_clicks.__setitem__("count", target_clicks["count"] + 1))
    target.resize(520, 220)
    target.show()

    window = MainWindow()
    window.show()
    _pump_until(app, lambda: window.isVisible() and target.isVisible(), 2.0)

    center = button.mapToGlobal(button.rect().center())
    screen_size = get_logical_screen_size()
    macro = build_stop_macro(
        screen_size=screen_size,
        button_xy=(center.x(), center.y()),
    )
    window._macro = macro
    window._editor.load_macro(macro)

    target.activateWindow()
    target.raise_()
    app.processEvents()

    hotkeys_registered = bool(window._hotkeys_registered)
    _press_function_key(0x76)  # VK_F7
    playback_started = _pump_until(
        app,
        lambda: window._state == "playing" and player.is_playing(),
        2.0,
    )

    stop_elapsed_s: float | None = None
    playback_stopped = False
    if playback_started:
        time.sleep(0.2)
        app.processEvents()
        stop_sent = time.perf_counter()
        _press_function_key(0x76)  # VK_F7 again -> stop
        playback_stopped = _pump_until(
            app,
            lambda: window._state == "idle" and not player.is_playing(),
            2.0,
        )
        if playback_stopped:
            stop_elapsed_s = time.perf_counter() - stop_sent

    _pump_until(app, lambda: False, 0.25)
    if player.is_playing():
        player.stop()

    result: dict[str, Any] = {
        "hotkeys_registered": hotkeys_registered,
        "playback_started": playback_started,
        "playback_stopped": playback_stopped,
        "stop_elapsed_s": stop_elapsed_s,
        "target_clicks": target_clicks["count"],
        "final_state": window._state,
        "screen_size": list(screen_size),
    }
    result["assertions"] = evaluate_hotkey_result(
        hotkeys_registered=hotkeys_registered,
        playback_started=playback_started,
        playback_stopped=playback_stopped,
        stop_elapsed_s=stop_elapsed_s,
        target_clicks=target_clicks["count"],
        final_state=window._state,
    )
    result["ok"] = all(result["assertions"].values())

    window.close()
    target.close()
    app.processEvents()
    return result


def _wait_macro(event_id: str, duration_ms: int) -> MacroData:
    event = WaitEvent(
        id=event_id,
        type="wait",
        timestamp_ns=0,
        duration_ms=duration_ms,
    )
    return MacroData(
        meta=_meta("Sequencer worker-to-Qt smoke"),
        settings=MacroSettings(),
        raw_events=[event],
        events=[event],
    )


def _run_sequencer_smoke(app: Any, work_dir: Path) -> dict[str, Any]:
    from PyQt6.QtCore import QThread

    from macroflow.macro_file import save
    from macroflow.ui.sequencer import MacroSequencerWidget

    first = work_dir / "first.json"
    second = work_dir / "second.json"
    save(_wait_macro("wait0001", 180), str(first))
    save(_wait_macro("wait0002", 180), str(second))

    widget = MacroSequencerWidget()
    widget.add_macro_file(first)
    widget.add_macro_file(second)
    widget.show()

    started: Counter[str] = Counter()
    finished: Counter[str] = Counter()
    gui_thread_updates: list[bool] = []
    completion_statuses: list[str] = []
    errors: list[str] = []

    widget._node_started.connect(lambda node_id, _label: started.update([node_id]))
    widget._node_finished.connect(lambda node_id, _success, _message: finished.update([node_id]))
    widget._list.model().dataChanged.connect(
        lambda *_args: gui_thread_updates.append(QThread.currentThread() is app.thread())
    )
    widget.sequence_complete.connect(completion_statuses.append)
    widget.sequence_error.connect(errors.append)

    widget.run_sequence()
    completed = _pump_until(
        app,
        lambda: widget._engine is None and bool(completion_statuses),
        8.0,
    )

    item_statuses = [item.status for item in widget._items]
    list_texts = [
        widget._list.item(index).text()
        for index in range(widget._list.count())
        if widget._list.item(index) is not None
    ]
    log_text = widget._log.toPlainText()
    result: dict[str, Any] = {
        "completed": completed,
        "completion_statuses": completion_statuses,
        "errors": errors,
        "item_statuses": item_statuses,
        "list_texts": list_texts,
        "started_counts": dict(started),
        "finished_counts": dict(finished),
        "gui_thread_updates": gui_thread_updates,
        "log_text": log_text,
    }
    result["assertions"] = evaluate_sequencer_result(
        completed=completed and not errors,
        item_statuses=item_statuses,
        list_texts=list_texts,
        started_counts=dict(started),
        finished_counts=dict(finished),
        gui_thread_updates=gui_thread_updates,
        log_text=log_text,
    )
    result["ok"] = all(result["assertions"].values())

    if widget.is_running():
        widget.stop_sequence()
    widget.close()
    app.processEvents()
    return result


def run_smoke(*, report_path: Path) -> dict[str, Any]:
    """Run both live Windows scenarios and write structured evidence."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "platform": os.name,
        "report_path": str(report_path),
    }
    with tempfile.TemporaryDirectory(prefix="macroflow-runtime-smoke-") as td:
        work_dir = Path(td)
        try:
            result["hotkey"] = _run_hotkey_smoke(app, work_dir)
        except Exception:
            result["hotkey"] = {"ok": False, "error": traceback.format_exc()}
        try:
            result["sequencer"] = _run_sequencer_smoke(app, work_dir)
        except Exception:
            result["sequencer"] = {"ok": False, "error": traceback.format_exc()}

    result["ok"] = bool(result["hotkey"].get("ok")) and bool(result["sequencer"].get("ok"))
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MacroFlow Windows runtime-safety smoke")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path.home() / "macroflow-rdp-test-logs" / "runtime_safety_smoke.json",
    )
    return parser.parse_args()


def format_status_line(result: dict[str, Any]) -> str:
    """Format a status line that remains printable on Windows cp949 consoles."""
    return "RUNTIME_SAFETY_STATUS=" + json.dumps(result, ensure_ascii=True)


def main() -> int:
    args = parse_args()
    result = run_smoke(report_path=args.report)
    print(format_status_line(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
