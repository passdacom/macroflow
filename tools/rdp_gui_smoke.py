"""Windows RDP GUI smoke harness for MacroFlow.

This script is intentionally a manual/Windows integration smoke, not a normal
pytest test. Run it inside the Windows RDP VM after installing MacroFlow in a
venv. It opens the deterministic ``tools/test_target_app.py`` Tk target window,
plays a MacroFlow scenario against it, and writes structured JSON/JSONL evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from macroflow import player
from macroflow.types import (
    ColorTriggerEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)
from macroflow.win32 import get_logical_screen_size

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from test_target_app import (  # noqa: E402
    DEFAULT_COLOR_HEX,
    DEFAULT_TEXT,
    DEFAULT_TITLE,
    TestTargetApp,
)

TARGET_TITLE = DEFAULT_TITLE


def _ratio(x: int, y: int, screen_size: tuple[int, int]) -> tuple[float, float]:
    screen_width, screen_height = screen_size
    return x / screen_width, y / screen_height


def _click_events(
    *,
    prefix: str,
    timestamp_ns: int,
    xy_ratio: tuple[float, float],
    color_check: bool = False,
) -> list[MouseButtonEvent]:
    down = MouseButtonEvent(
        id=f"{prefix}dn",
        type="mouse_down",
        timestamp_ns=timestamp_ns,
        x_ratio=xy_ratio[0],
        y_ratio=xy_ratio[1],
        button="left",
        recorded_color="#000000" if color_check else None,
        color_check_enabled=color_check,
        color_check_on_mismatch="wait",
    )
    up = MouseButtonEvent(
        id=f"{prefix}up",
        type="mouse_up",
        timestamp_ns=timestamp_ns + 80_000_000,
        x_ratio=xy_ratio[0],
        y_ratio=xy_ratio[1],
        button="left",
    )
    return [down, up]


def build_smoke_macro(
    *,
    screen_size: tuple[int, int],
    button_xy: tuple[int, int],
    entry_xy: tuple[int, int],
    color_xy: tuple[int, int],
    drag_xy: tuple[int, int] | None = None,
    wheel_xy: tuple[int, int] | None = None,
    color_hex: str = DEFAULT_COLOR_HEX,
    text: str = DEFAULT_TEXT,
) -> MacroData:
    """Build the deterministic MacroFlow scenario used by the RDP smoke test."""
    button_ratio = _ratio(*button_xy, screen_size)
    entry_ratio = _ratio(*entry_xy, screen_size)
    color_ratio = _ratio(*color_xy, screen_size)
    meta = MacroMeta(
        version="1",
        app_version="rdp-smoke",
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        screen_width=screen_size[0],
        screen_height=screen_size[1],
        dpi_scale=1.0,
    )
    settings = MacroSettings(
        color_check_click_wait_timeout_ms=300,
        color_check_click_interval_ms=50,
        color_check_click_tolerance=0,
        color_trigger_default_timeout_ms=1000,
        color_trigger_check_interval_ms=50,
    )
    events: list[Any] = [
        WindowTriggerEvent(
            id="win00001",
            type="window_trigger",
            timestamp_ns=0,
            window_title_contains=TARGET_TITLE,
            timeout_ms=2000,
            on_timeout="error",
        ),
        *_click_events(prefix="btn001", timestamp_ns=100_000_000, xy_ratio=button_ratio, color_check=True),
        WaitEvent(id="wait0001", type="wait", timestamp_ns=650_000_000, duration_ms=120),
        *_click_events(prefix="ent001", timestamp_ns=950_000_000, xy_ratio=entry_ratio),
        TextInputEvent(id="text0001", type="text_input", timestamp_ns=1_300_000_000, text=text),
        ColorTriggerEvent(
            id="col00001",
            type="color_trigger",
            timestamp_ns=1_650_000_000,
            x_ratio=color_ratio[0],
            y_ratio=color_ratio[1],
            target_color=color_hex,
            tolerance=4,
            timeout_ms=1000,
            check_interval_ms=50,
            on_timeout="error",
        ),
        *_click_events(prefix="col001", timestamp_ns=1_850_000_000, xy_ratio=color_ratio),
    ]

    next_ts = 2_250_000_000
    if drag_xy is not None:
        drag_ratio = _ratio(*drag_xy, screen_size)
        drag_end_ratio = _ratio(drag_xy[0] + 80, drag_xy[1] + 25, screen_size)
        events.extend(
            [
                MouseButtonEvent(
                    id="drg00001",
                    type="mouse_down",
                    timestamp_ns=next_ts,
                    x_ratio=drag_ratio[0],
                    y_ratio=drag_ratio[1],
                    button="left",
                ),
                MouseMoveEvent(
                    id="drg00002",
                    type="mouse_move",
                    timestamp_ns=next_ts + 140_000_000,
                    x_ratio=drag_end_ratio[0],
                    y_ratio=drag_end_ratio[1],
                ),
                MouseButtonEvent(
                    id="drg00003",
                    type="mouse_up",
                    timestamp_ns=next_ts + 260_000_000,
                    x_ratio=drag_end_ratio[0],
                    y_ratio=drag_end_ratio[1],
                    button="left",
                ),
            ]
        )
        next_ts += 520_000_000

    if wheel_xy is not None:
        wheel_ratio = _ratio(*wheel_xy, screen_size)
        events.append(
            MouseWheelEvent(
                id="whl00001",
                type="mouse_wheel",
                timestamp_ns=next_ts,
                x_ratio=wheel_ratio[0],
                y_ratio=wheel_ratio[1],
                delta=-120,
                axis="vertical",
            )
        )

    return MacroData(meta=meta, settings=settings, raw_events=events, events=events)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_gui_smoke(*, log_dir: Path, text: str = DEFAULT_TEXT) -> dict[str, Any]:
    """Run the GUI smoke test and return the structured status payload."""
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    events_path = log_dir / f"gui_events_{stamp}.jsonl"
    status_path = log_dir / f"gui_status_{stamp}.json"

    app = TestTargetApp(
        status_path=status_path,
        events_path=events_path,
        scenario="rdp-gui-smoke",
        expected_text=text,
        color_hex=DEFAULT_COLOR_HEX,
        title=TARGET_TITLE,
    )
    app.build()
    status = app.status
    status["play_events"] = []
    status["playback_errors"] = []

    def run_playback() -> None:
        try:
            app.focus()
            app.reset_interaction_state()
            screen_size = get_logical_screen_size()
            coords = status["coords"]
            status["coords"] = {**coords, "screen": list(screen_size)}
            app.write_status()
            app.log("coords", **status["coords"])
            macro = build_smoke_macro(
                screen_size=screen_size,
                button_xy=tuple(coords["button"]),
                entry_xy=tuple(coords["entry"]),
                color_xy=tuple(coords["color"]),
                drag_xy=tuple(coords["drag"]),
                wheel_xy=tuple(coords["wheel"]),
                color_hex=DEFAULT_COLOR_HEX,
                text=text,
            )
            complete = {"ok": False}
            errors: list[str] = []
            started = time.perf_counter()

            def on_event(idx: int, event: object) -> None:
                status["play_events"].append(
                    {"idx": idx, "type": getattr(event, "type", ""), "dt": round(time.perf_counter() - started, 3)}
                )
                app.log("play_event", idx=idx, type=getattr(event, "type", ""))

            def on_complete() -> None:
                complete["ok"] = True
                app.log("complete")

            def on_error(error: Exception) -> None:
                errors.append(str(error))
                app.log("error", error=str(error))

            player.play(macro, on_event=on_event, on_complete=on_complete, on_error=on_error)
            deadline = time.time() + 10
            while player.is_playing() and time.time() < deadline:
                assert app.root is not None
                app.root.update()
                app._set_text_value()
                time.sleep(0.02)
            assert app.root is not None
            app.root.update()
            app._set_text_value()
            if player.is_playing():
                player.stop()
                errors.append("playback timed out")
            target_assertions = status.get("assertions", {})
            playback_assertions = {
                "window_trigger_ok": len(status["play_events"]) >= 1,
                "complete_callback_ok": complete["ok"],
                "no_playback_error": not errors,
            }
            status["assertions"] = {**target_assertions, **playback_assertions}
            status["ok"] = all(status["assertions"].values())
            status["playback_errors"] = errors
        except Exception:  # pragma: no cover - Windows/RDP evidence path
            status["error"] = traceback.format_exc()
            status["ok"] = False
        finally:
            _write_json(status_path, status)
            app.log("status_written", status=str(status_path), ok=status.get("ok"))
            app.destroy_after(300)

    app.after(700, run_playback)
    app.mainloop()
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MacroFlow Windows RDP GUI smoke test")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path.home() / "macroflow-rdp-test-logs",
        help="Directory for JSON/JSONL evidence logs",
    )
    parser.add_argument("--text", default=DEFAULT_TEXT, help="TextInputEvent payload to verify")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status = run_gui_smoke(log_dir=args.log_dir, text=args.text)
    print("GUI_SMOKE_STATUS=" + json.dumps(status, ensure_ascii=False))
    return 0 if status.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
