"""Live Windows/Linux QA harness for the MacroFlow status overlay."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from macroflow.ui.overlay import OverlayWindow


def _inside(inner: object, outer: object) -> bool:
    return (
        outer.left() <= inner.left()
        and outer.top() <= inner.top()
        and inner.right() <= outer.right()
        and inner.bottom() <= outer.bottom()
    )


def run_smoke(report_path: Path) -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    overlay = OverlayWindow()
    screen = app.primaryScreen()
    if screen is None:
        raise RuntimeError("사용 가능한 화면이 없습니다")
    available = screen.availableGeometry()

    overlay.start_recording()
    overlay.set_event_count(123)
    app.processEvents()
    recording_text = overlay._recording_text(0.0)
    recording_visible = overlay.isVisible()

    drag_start = overlay.pos()
    QTest.mousePress(overlay, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    QTest.mouseMove(overlay, QPoint(60, 30), delay=10)
    QTest.mouseRelease(overlay, Qt.MouseButton.LeftButton, pos=QPoint(60, 30))
    app.processEvents()
    drag_delta = overlay.pos() - drag_start
    drag_moved = drag_delta != QPoint(0, 0)

    overlay.start_playing(2.0, repeat_current=100, repeat_total=999)
    overlay.set_progress(0.42)
    app.processEvents()
    playing_text = overlay._playing_text()
    metrics = QFontMetrics(overlay._status_font())
    required_width = 36 + metrics.horizontalAdvance(playing_text) + 12
    playing_width = overlay.width()
    playing_geometry = overlay.geometry()
    image_path = report_path.with_suffix(".png")
    image_path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = overlay.grab()
    image_saved = pixmap.save(str(image_path))
    background_alpha = pixmap.toImage().pixelColor(20, 10).alpha()

    overlay.start_flowing(1.5, current=2, total=3)
    app.processEvents()
    flowing_text = overlay._flowing_text()
    flow_visible = overlay.isVisible()

    overlay.stop()
    app.processEvents()
    stopped_hidden = not overlay.isVisible()
    timers_stopped = not overlay._repaint_timer.isActive() and not overlay._blink_timer.isActive()

    assertions = {
        "recording_visible": recording_visible,
        "recording_count_visible": recording_text.endswith("#123"),
        "repeat_text_exact": playing_text == "PLAY  100/999회  42%  2.0x",
        "repeat_not_clipped": playing_width >= required_width,
        "translucent_background": overlay.testAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        ),
        "painted_background_translucent": 0 < background_alpha < 255,
        "stays_on_top": bool(overlay.windowFlags() & Qt.WindowType.WindowStaysOnTopHint),
        "inside_available_work_area": _inside(playing_geometry, available),
        "drag_moves_overlay": drag_moved,
        "flow_visible": flow_visible,
        "flow_text_exact": flowing_text == "FLOW  2/3  1.5x",
        "stop_hides_overlay": stopped_hidden,
        "stop_stops_timers": timers_stopped,
        "screenshot_saved": image_saved and image_path.exists(),
    }
    result: dict[str, object] = {
        "ok": all(assertions.values()),
        "platform": os.name,
        "screen_name": screen.name(),
        "device_pixel_ratio": screen.devicePixelRatio(),
        "available_geometry": [
            available.x(),
            available.y(),
            available.width(),
            available.height(),
        ],
        "overlay_geometry": [
            playing_geometry.x(),
            playing_geometry.y(),
            playing_geometry.width(),
            playing_geometry.height(),
        ],
        "recording_text": recording_text,
        "playing_text": playing_text,
        "flowing_text": flowing_text,
        "required_width": required_width,
        "actual_width": playing_width,
        "background_alpha": background_alpha,
        "drag_delta": [drag_delta.x(), drag_delta.y()],
        "screenshot": str(image_path),
        "assertions": assertions,
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    overlay.deleteLater()
    app.processEvents()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MacroFlow overlay live smoke")
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_smoke(args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
