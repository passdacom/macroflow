"""MacroFlow 미니 오버레이 창.

녹화·재생·플로우 실행 중 화면 우하단에 항상 최상위로 표시된다.
상태 텍스트 길이에 맞춰 폭을 늘리며 드래그 이동할 수 있다.
"""

from __future__ import annotations

import time

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPolygon,
)
from PyQt6.QtWidgets import QApplication, QWidget


class OverlayWindow(QWidget):
    """녹화/재생/플로우/힌트 상태를 표시하는 미니 플로팅 창."""

    _MIN_WIDTH = 210
    _HEIGHT = 52

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self._MIN_WIDTH, self._HEIGHT)

        self._mode: str = "recording"  # recording | playing | flowing | hint
        self._hint_text: str = ""
        self._start_time: float = 0.0
        self._event_count: int = 0
        self._progress: float = 0.0
        self._speed: float = 1.0
        self._repeat_current: int = 1
        self._repeat_total: int = 1
        self._flow_current: int = 1
        self._flow_total: int = 1
        self._paused: bool = False
        self._pause_started: float | None = None
        self._paused_total: float = 0.0
        self._blink_on: bool = True
        self._drag_offset: QPoint = QPoint(0, 0)
        self._dragging: bool = False

        self._repaint_timer = QTimer(self)
        self._repaint_timer.timeout.connect(self._tick)
        self._repaint_timer.setInterval(500)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.setInterval(800)

        self._position_bottom_right()

    def _position_bottom_right(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(
                geom.right() - self.width() - 16,
                geom.bottom() - self.height() - 16,
            )

    @staticmethod
    def _status_font(point_size: int = 10) -> QFont:
        font = QFont()
        font.setPointSize(point_size)
        font.setBold(True)
        return font

    def _sync_width_for_text(
        self,
        text: str,
        *,
        text_x: int = 36,
        point_size: int = 10,
    ) -> None:
        """텍스트가 잘리지 않게 폭을 늘리고 표시 중이면 오른쪽 끝 위치를 유지한다."""
        metrics = QFontMetrics(self._status_font(point_size))
        required = text_x + metrics.horizontalAdvance(text) + 12
        new_width = max(self._MIN_WIDTH, required)
        if new_width == self.width():
            return
        old_right = self.geometry().right()
        was_visible = self.isVisible()
        self.setFixedSize(new_width, self._HEIGHT)
        if was_visible:
            self.move(old_right - new_width + 1, self.y())

    def _recording_text(self, elapsed: float) -> str:
        mm = int(elapsed) // 60
        ss = int(elapsed) % 60
        prefix = "PAUSE · REC" if self._paused else "REC"
        return f"{prefix}  {mm:02d}:{ss:02d}  #{self._event_count}"

    def _playing_text(self) -> str:
        pct = int(self._progress * 100)
        prefix = "PAUSE · PLAY" if self._paused else "PLAY"
        if self._repeat_total > 1:
            return (
                f"{prefix}  {self._repeat_current}/{self._repeat_total}회  "
                f"{pct}%  {self._speed:.1f}x"
            )
        return f"{prefix}  {pct}%  {self._speed:.1f}x"

    def _flowing_text(self) -> str:
        return f"FLOW  {self._flow_current}/{self._flow_total}  {self._speed:.1f}x"

    # ── 공개 제어 인터페이스 ───────────────────────────────────────────────────

    def _show_on_top(self) -> None:
        """오버레이를 현재 화면 우하단에 다시 배치하고 최상단으로 표시한다."""
        self._position_bottom_right()
        self.show()
        self.raise_()
        self.update()

    def _reset_pause(self) -> None:
        self._paused = False
        self._pause_started = None
        self._paused_total = 0.0

    def _recording_elapsed(self) -> float:
        """pause 구간을 제외한 녹화 active elapsed seconds를 반환한다."""
        now = self._pause_started if self._paused else time.monotonic()
        assert now is not None
        return max(0.0, now - self._start_time - self._paused_total)

    def start_recording(self) -> None:
        """녹화 모드로 오버레이를 표시한다."""
        self._mode = "recording"
        self._reset_pause()
        self._start_time = time.monotonic()
        self._event_count = 0
        self._blink_on = True
        self._repaint_timer.start()
        self._blink_timer.start()
        self._sync_width_for_text(self._recording_text(0.0), text_x=34)
        self._show_on_top()

    def start_playing(
        self,
        speed: float = 1.0,
        *,
        repeat_current: int = 1,
        repeat_total: int = 1,
    ) -> None:
        """재생 모드로 오버레이를 표시한다."""
        self._mode = "playing"
        self._reset_pause()
        self._start_time = time.monotonic()
        self._progress = 0.0
        self._speed = speed
        self.set_repeat(repeat_current, repeat_total)
        self._repaint_timer.start()
        self._blink_timer.stop()
        self._show_on_top()

    def start_flowing(
        self,
        speed: float = 1.0,
        *,
        current: int = 1,
        total: int = 1,
    ) -> None:
        """시퀀스/플로우 실행 모드로 오버레이를 표시한다."""
        self._mode = "flowing"
        self._start_time = time.monotonic()
        self._speed = speed
        self.set_flow_progress(current, total)
        self._repaint_timer.start()
        self._blink_timer.stop()
        self._show_on_top()

    def set_event_count(self, count: int) -> None:
        """녹화 중 이벤트 수를 갱신한다."""
        self._event_count = count
        self._sync_width_for_text(
            self._recording_text(self._recording_elapsed()),
            text_x=34,
        )
        self.update()

    def set_paused(self, paused: bool) -> None:
        """녹화/재생 pause 표시와 녹화 active elapsed clock을 전환한다."""
        if paused == self._paused:
            return
        now = time.monotonic()
        if paused:
            self._paused = True
            self._pause_started = now
            self._blink_timer.stop()
            self._blink_on = True
        else:
            assert self._pause_started is not None
            self._paused_total += max(0.0, now - self._pause_started)
            self._pause_started = None
            self._paused = False
            if self._mode == "recording":
                self._blink_timer.start()
        text = (
            self._recording_text(self._recording_elapsed())
            if self._mode == "recording"
            else self._playing_text()
        )
        self._sync_width_for_text(text, text_x=34 if self._mode == "recording" else 36)
        self.update()

    def set_progress(self, progress: float) -> None:
        """재생 진행률(0.0~1.0)을 갱신한다."""
        self._progress = max(0.0, min(1.0, progress))
        self._sync_width_for_text(self._playing_text())
        self.update()

    def set_repeat(self, current: int, total: int) -> None:
        """반복 재생 상태를 갱신한다."""
        self._repeat_total = max(1, total)
        self._repeat_current = min(max(1, current), self._repeat_total)
        self._sync_width_for_text(self._playing_text())
        self.update()

    def set_flow_progress(self, current: int, total: int) -> None:
        """시퀀스의 현재/전체 매크로 순번을 갱신한다."""
        self._flow_total = max(1, total)
        self._flow_current = min(max(1, current), self._flow_total)
        self._sync_width_for_text(self._flowing_text())
        self.update()

    def show_hint(self, text: str) -> None:
        """F6 캡처 대기 중 힌트 메시지를 표시한다."""
        self._mode = "hint"
        self._hint_text = text
        self._repaint_timer.stop()
        self._blink_timer.stop()
        self._sync_width_for_text(text, text_x=34, point_size=9)
        self._show_on_top()

    def stop_hint(self) -> None:
        """힌트 모드를 종료한다."""
        if self._mode == "hint":
            self.hide()

    def stop(self) -> None:
        """오버레이를 숨기고 타이머를 중지한다."""
        self._repaint_timer.stop()
        self._blink_timer.stop()
        self.hide()

    # ── 내부 ──────────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if self._mode == "recording":
            self._sync_width_for_text(
                self._recording_text(self._recording_elapsed()),
                text_x=34,
            )
        self.update()

    def _toggle_blink(self) -> None:
        self._blink_on = not self._blink_on
        self.update()

    # ── 페인트 ────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(24, 24, 28, 225))
        painter.setPen(QColor(70, 70, 80, 180))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)

        elapsed = self._recording_elapsed() if self._mode == "recording" else 0.0
        if self._mode == "recording":
            self._paint_recording(painter, elapsed)
        elif self._mode == "hint":
            self._paint_hint(painter)
        elif self._mode == "flowing":
            self._paint_flowing(painter)
        else:
            self._paint_playing(painter)

        painter.end()

    def _paint_recording(self, painter: QPainter, elapsed: float) -> None:
        painter.setBrush(QColor(230, 55, 55) if self._blink_on else QColor(90, 30, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(14, 18, 14, 14)

        painter.setFont(self._status_font())
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            34,
            0,
            self.width() - 40,
            self.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._recording_text(elapsed),
        )

    def _paint_playing(self, painter: QPainter) -> None:
        painter.setBrush(QColor(55, 210, 95))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygon([QPoint(12, 14), QPoint(12, 38), QPoint(28, 26)]))

        painter.setFont(self._status_font())
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            36,
            0,
            self.width() - 42,
            self.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._playing_text(),
        )

    def _paint_flowing(self, painter: QPainter) -> None:
        painter.setBrush(QColor(70, 150, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygon([QPoint(12, 14), QPoint(12, 38), QPoint(28, 26)]))

        painter.setFont(self._status_font())
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            36,
            0,
            self.width() - 42,
            self.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._flowing_text(),
        )

    def _paint_hint(self, painter: QPainter) -> None:
        """F6 캡처 대기 힌트 메시지를 그린다."""
        painter.setBrush(QColor(220, 170, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 16, 18, 18)

        painter.setFont(self._status_font(9))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            34,
            0,
            self.width() - 40,
            self.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._hint_text,
        )

    # ── 드래그 이동 ───────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        if event and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self._dragging = True

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        if event and self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        self._dragging = False
