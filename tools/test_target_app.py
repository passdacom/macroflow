"""Deterministic Tk target app for MacroFlow Windows/RDP integration tests.

The app is intentionally small and dependency-free.  It gives MacroFlow a stable
native GUI surface to click/type/drag/scroll against and writes structured JSON
status plus JSONL event evidence so RDP smoke runs are assertable without relying
on screenshots.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

DEFAULT_TITLE = "MacroFlow RDP Smoke Target"
DEFAULT_COLOR_HEX = "#22AA55"
DEFAULT_TEXT = "rdp-ok"


def normalize_color_hex(color_hex: str) -> str:
    """Return a normalized #RRGGBB color string."""
    value = color_hex.strip().upper()
    if not value.startswith("#"):
        value = f"#{value}"
    if len(value) != 7:
        raise ValueError(f"expected #RRGGBB color, got {color_hex!r}")
    int(value[1:], 16)
    return value


def initial_status(
    *,
    scenario: str,
    status_path: Path,
    events_path: Path,
    color_hex: str = DEFAULT_COLOR_HEX,
    title: str = DEFAULT_TITLE,
) -> dict[str, Any]:
    """Build the stable status schema used by smoke harnesses and humans."""
    return {
        "scenario": scenario,
        "title": title,
        "ready": False,
        "ok": False,
        "error": None,
        "button_clicks": 0,
        "text_value": "",
        "color_clicks": 0,
        "drag_count": 0,
        "wheel_delta": 0,
        "color_hex": normalize_color_hex(color_hex),
        "coords": {},
        "assertions": {},
        "status_path": str(status_path),
        "events_path": str(events_path),
    }


def write_status(path: Path, status: dict[str, Any]) -> None:
    """Persist the latest status as human-readable UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def append_event(path: Path, kind: str, **payload: Any) -> None:
    """Append one structured evidence record to the target app event log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"t": time.perf_counter(), "kind": kind, **payload}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_assertions(status: dict[str, Any], *, expected_text: str = DEFAULT_TEXT) -> dict[str, bool]:
    """Return target-side assertions for all v1 interaction surfaces."""
    return {
        "button_clicked": int(status.get("button_clicks", 0)) >= 1,
        "text_input_ok": status.get("text_value") == expected_text,
        "color_clicked": int(status.get("color_clicks", 0)) >= 1,
        "drag_seen": int(status.get("drag_count", 0)) >= 1,
        "wheel_seen": int(status.get("wheel_delta", 0)) != 0,
    }


def is_success(assertions: dict[str, bool]) -> bool:
    return bool(assertions) and all(assertions.values())


class TestTargetApp:
    """Small Tk GUI that exposes stable targets and status evidence."""

    def __init__(
        self,
        *,
        status_path: Path,
        events_path: Path,
        scenario: str = "basic",
        expected_text: str = DEFAULT_TEXT,
        color_hex: str = DEFAULT_COLOR_HEX,
        title: str = DEFAULT_TITLE,
        geometry: str = "720x520+120+140",
        topmost: bool = True,
    ) -> None:
        self.status_path = status_path
        self.events_path = events_path
        self.scenario = scenario
        self.expected_text = expected_text
        self.color_hex = normalize_color_hex(color_hex)
        self.title = title
        self.geometry = geometry
        self.topmost = topmost
        self.status = initial_status(
            scenario=scenario,
            status_path=status_path,
            events_path=events_path,
            color_hex=self.color_hex,
            title=title,
        )
        self.root: Any = None
        self.button: Any = None
        self.entry: Any = None
        self.color_canvas: Any = None
        self.drag_canvas: Any = None
        self.wheel_canvas: Any = None
        self._drag_start: tuple[int, int] | None = None

    def log(self, kind: str, **payload: Any) -> None:
        append_event(self.events_path, kind, **payload)

    def _set_text_value(self) -> None:
        if self.entry is not None:
            self.status["text_value"] = self.entry.get()

    def _refresh_assertions(self) -> None:
        self._set_text_value()
        assertions = build_assertions(self.status, expected_text=self.expected_text)
        self.status["assertions"] = assertions
        self.status["ok"] = is_success(assertions)

    def write_status(self) -> None:
        self._refresh_assertions()
        write_status(self.status_path, self.status)

    def _center(self, widget: Any) -> tuple[int, int]:
        assert self.root is not None
        self.root.update_idletasks()
        return widget.winfo_rootx() + widget.winfo_width() // 2, widget.winfo_rooty() + widget.winfo_height() // 2

    def coords(self) -> dict[str, list[int]]:
        """Return absolute screen coordinates for all target centers."""
        assert self.button is not None
        assert self.entry is not None
        assert self.color_canvas is not None
        assert self.drag_canvas is not None
        assert self.wheel_canvas is not None
        return {
            "button": list(self._center(self.button)),
            "entry": list(self._center(self.entry)),
            "color": list(self._center(self.color_canvas)),
            "drag": list(self._center(self.drag_canvas)),
            "wheel": list(self._center(self.wheel_canvas)),
        }

    def mark_ready(self) -> None:
        self.status["ready"] = True
        self.status["coords"] = self.coords()
        self.write_status()
        self.log("ready", coords=self.status["coords"])

    def focus(self) -> None:
        assert self.root is not None
        self.root.lift()
        self.root.focus_force()

    def reset_interaction_state(self) -> None:
        """Reset counters while preserving readiness and target coordinates."""
        self.status.update(
            {
                "ok": False,
                "error": None,
                "button_clicks": 0,
                "text_value": "",
                "color_clicks": 0,
                "drag_count": 0,
                "wheel_delta": 0,
                "assertions": {},
            }
        )
        if self.entry is not None:
            self.entry.delete(0, "end")
        self.write_status()
        self.log("reset")

    def build(self) -> None:
        import tkinter as tk

        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry(self.geometry)
        self.root.configure(bg="white")
        if self.topmost:
            self.root.attributes("-topmost", True)

        label = tk.Label(
            self.root,
            text="MacroFlow Test Target",
            font=("Segoe UI", 16),
            bg="white",
        )
        label.place(x=20, y=18)
        hint = tk.Label(
            self.root,
            text="button / text / color / drag / wheel surfaces write JSON evidence",
            font=("Segoe UI", 9),
            bg="white",
        )
        hint.place(x=22, y=50)

        self.button = tk.Button(self.root, text="CLICK_TARGET", width=18, height=2, command=self._on_button)
        self.button.place(x=80, y=100)

        self.entry = tk.Entry(self.root, width=28, font=("Segoe UI", 14))
        self.entry.place(x=80, y=190)
        self.entry.bind("<KeyRelease>", self._on_text_change)
        self.entry.bind("<FocusOut>", self._on_text_change)

        self.color_canvas = tk.Canvas(
            self.root,
            width=100,
            height=100,
            bg=self.color_hex,
            highlightthickness=1,
            highlightbackground="#444444",
        )
        self.color_canvas.place(x=460, y=95)
        self.color_canvas.bind("<Button-1>", self._on_color_click)

        self.drag_canvas = tk.Canvas(
            self.root,
            width=170,
            height=80,
            bg="#E8F0FE",
            highlightthickness=1,
            highlightbackground="#5577AA",
        )
        self.drag_canvas.place(x=80, y=310)
        self.drag_canvas.create_text(85, 40, text="DRAG_TARGET", fill="#1F3B68")
        self.drag_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.drag_canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        self.wheel_canvas = tk.Canvas(
            self.root,
            width=170,
            height=80,
            bg="#FFF4D6",
            highlightthickness=1,
            highlightbackground="#AA8844",
        )
        self.wheel_canvas.place(x=390, y=310)
        self.wheel_canvas.create_text(85, 40, text="WHEEL_TARGET", fill="#654A00")
        self.wheel_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.wheel_canvas.bind("<Button-4>", self._on_mouse_wheel_linux)
        self.wheel_canvas.bind("<Button-5>", self._on_mouse_wheel_linux)

        self.root.update()
        self.mark_ready()

    def _on_button(self) -> None:
        self.status["button_clicks"] = int(self.status["button_clicks"]) + 1
        self.write_status()
        self.log("button_click", count=self.status["button_clicks"])

    def _on_text_change(self, _event: object | None = None) -> None:
        self._set_text_value()
        self.write_status()
        self.log("text_change", value=self.status["text_value"])

    def _on_color_click(self, _event: object) -> None:
        self.status["color_clicks"] = int(self.status["color_clicks"]) + 1
        self.write_status()
        self.log("color_click", count=self.status["color_clicks"])

    def _on_drag_start(self, event: Any) -> None:
        self._drag_start = (event.x_root, event.y_root)
        self.log("drag_start", x=event.x_root, y=event.y_root)

    def _on_drag_end(self, event: Any) -> None:
        if self._drag_start is None:
            return
        dx = event.x_root - self._drag_start[0]
        dy = event.y_root - self._drag_start[1]
        if abs(dx) >= 5 or abs(dy) >= 5:
            self.status["drag_count"] = int(self.status["drag_count"]) + 1
            self.write_status()
            self.log("drag_end", count=self.status["drag_count"], dx=dx, dy=dy)
        self._drag_start = None

    def _on_mouse_wheel(self, event: Any) -> None:
        self.status["wheel_delta"] = int(self.status["wheel_delta"]) + int(event.delta)
        self.write_status()
        self.log("wheel", delta=event.delta, total=self.status["wheel_delta"])

    def _on_mouse_wheel_linux(self, event: Any) -> None:
        delta = 120 if getattr(event, "num", 0) == 4 else -120
        self.status["wheel_delta"] = int(self.status["wheel_delta"]) + delta
        self.write_status()
        self.log("wheel", delta=delta, total=self.status["wheel_delta"])

    def after(self, delay_ms: int, callback: Any) -> None:
        assert self.root is not None
        self.root.after(delay_ms, callback)

    def destroy_after(self, delay_ms: int = 300) -> None:
        assert self.root is not None
        self.root.after(delay_ms, self.root.destroy)

    def mainloop(self) -> None:
        assert self.root is not None
        self.root.mainloop()


def run_target_app(
    *,
    status_path: Path,
    events_path: Path,
    scenario: str = "basic",
    expected_text: str = DEFAULT_TEXT,
    color_hex: str = DEFAULT_COLOR_HEX,
    title: str = DEFAULT_TITLE,
) -> dict[str, Any]:
    app = TestTargetApp(
        status_path=status_path,
        events_path=events_path,
        scenario=scenario,
        expected_text=expected_text,
        color_hex=color_hex,
        title=title,
    )
    app.build()
    app.mainloop()
    return app.status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MacroFlow deterministic Tk test target app")
    parser.add_argument("--status", type=Path, required=True, help="Path for target_status.json")
    parser.add_argument("--events", type=Path, required=True, help="Path for target_events.jsonl")
    parser.add_argument("--scenario", default="basic", help="Scenario label written into evidence")
    parser.add_argument("--expected-text", default=DEFAULT_TEXT, help="Expected text for target assertions")
    parser.add_argument("--color", default=DEFAULT_COLOR_HEX, help="Target color box #RRGGBB")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Window title")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status = run_target_app(
        status_path=args.status,
        events_path=args.events,
        scenario=args.scenario,
        expected_text=args.expected_text,
        color_hex=args.color,
        title=args.title,
    )
    print("TARGET_STATUS=" + json.dumps(status, ensure_ascii=False))
    return 0 if status.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
