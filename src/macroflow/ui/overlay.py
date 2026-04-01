"""MacroFlow 미니 오버레이 창.

녹화·재생 중 화면 우하단에 항상 최상위로 표시된다.
크기: 200×52px. 드래그 이동 가능.
"""

from __future__ import annotations

import time

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPolygon,
)
from PyQt6.QtWidgets import QApplication, QWidget


class OverlayWindow(QWidget):
    """녹화/재생/힌트 상태를 표시하는 미니 플로팅 창."""

    _WIDTH = 210
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
        self.setFixedSize(self._WIDTH, self._HEIGHT)

        self._mode: str = "recording"  # "recording" | "playing" | "hint"
        self._hint_text: str = ""
        self._start_time: float = 0.0
        self._event_count: int = 0
        self._progress: float = 0.0
        self._speed: float = 1.0
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
            self.move(geom.right() - self._WIDTH - 16,
                      geom.bottom() - self._HEIGHT - 16)

    # ── 공개 제어 인터페이스 ───────────────────────────────────────────────────

    def start_recording(self) -> None:
        """녹화 모드로 오버레이를 표시한다."""
        self._mode = "recording"
        self._start_time = time.monotonic()
        self._event_count = 0
        self._blink_on = True
        self._repaint_timer.start()
        self._blink_timer.start()
        self.show()

    def start_playing(self, speed: float = 1.0) -> None:
        """재생 모드로 오버레이를 표시한다."""
        self._mode = "playing"
        self._start_time = time.monotonic()
        self._progress = 0.0
        self._speed = speed
        self._repaint_timer.start()
        self._blink_timer.stop()
        self.show()

    def set_event_count(self, count: int) -> None:
        """녹화 중 이벤트 수를 갱신한다."""
        self._event_count = count

    def set_progress(self, progress: float) -> None:
        """재생 진행률(0.0~1.0)을 갱신한다."""
        self._progress = max(0.0, min(1.0, progress))

    def show_hint(self, text: str) -> None:
        """F6 캡처 대기 중 힌트 메시지를 표시한다."""
        self._mode = "hint"
        self._hint_text = text
        self._repaint_timer.stop()
        self._blink_timer.stop()
        self._position_bottom_right()
        self.show()
        self.update()

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
        self.update()

    def _toggle_blink(self) -> None:
        self._blink_on = not self._blink_on
        self.update()

    # ── 페인트 ────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        painter.setBrush(QColor(24, 24, 28, 225))
        painter.setPen(QColor(70, 70, 80, 180))
        painter.drawRoundedRect(1, 1, self._WIDTH - 2, self._HEIGHT - 2, 10, 10)

        elapsed = time.monotonic() - self._start_time

        if self._mode == "recording":
            self._paint_recording(painter, elapsed)
        elif self._mode == "hint":
            self._paint_hint(painter)
        else:
            self._paint_playing(painter)

        painter.end()

    def _paint_recording(self, painter: QPainter, elapsed: float) -> None:
        # 빨간 점 (깜빡임)
        if self._blink_on:
            painter.setBrush(QColor(230, 55, 55))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(14, 18, 14, 14)
        else:
            painter.setBrush(QColor(90, 30, 30))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(14, 18, 14, 14)

        mm = int(elapsed) // 60
        ss = int(elapsed) % 60
        text = f"REC  {mm:02d}:{ss:02d}  #{self._event_count}"

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(34, 0, self._WIDTH - 40, self._HEIGHT,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         text)

    def _paint_playing(self, painter: QPainter) -> None:
        # 초록 재생 삼각형
        painter.setBrush(QColor(55, 210, 95))
        painter.setPen(Qt.PenStyle.NoPen)
        tri = QPolygon([QPoint(12, 14), QPoint(12, 38), QPoint(28, 26)])
        painter.drawPolygon(tri)

        pct = int(self._progress * 100)
        text = f"PLAY  {pct}%  {self._speed:.1f}x"

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(36, 0, self._WIDTH - 42, self._HEIGHT,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         text)

    def _paint_hint(self, painter: QPainter) -> None:
        """F6 캡처 대기 힌트 메시지를 그린다."""
        # 노란 📍 아이콘 영역
        painter.setBrush(QColor(220, 170, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 16, 18, 18)

        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(34, 0, self._WIDTH - 40, self._HEIGHT,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         self._hint_text)

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
