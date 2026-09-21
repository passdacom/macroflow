"""Cancelable preparation and read-only foreground checks for partial input."""
from __future__ import annotations

import os
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget


def external_target_ready(*, check_modifiers: bool = True) -> bool:
    """Fail closed unless an external process owns focus; never release user keys."""
    if sys.platform != "win32":
        return False
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    hwnd = user32.GetForegroundWindow()
    pid = wintypes.DWORD()
    if not hwnd or not user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)):
        return False
    if pid.value in (0, os.getpid()):
        return False
    return not check_modifiers or not any(
        user32.GetAsyncKeyState(vk) & 0x8000 for vk in (16, 17, 18, 91, 92))


class RangePreparationDialog(QDialog):
    def __init__(self, parent: QWidget, start: int, end: int) -> None:
        super().__init__(parent)
        self.setWindowTitle("선택 구간 1회 재생 준비")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"이벤트 {start + 1}~{end}만 1회 실행합니다.\n"
            "대상 창으로 전환하고 필요한 선택·클립보드 상태를 준비하세요.\n"
            "선택 밖의 선행 동작은 실행되지 않습니다.", self))
        self.remaining = 3
        self.label = QLabel("3초 후 시작", self)
        layout.addWidget(self.label)
        cancel = QPushButton("취소", self)
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _tick(self) -> None:
        self.remaining -= 1
        self.label.setText(f"{self.remaining}초 후 시작")
        if self.remaining <= 0:
            self.timer.stop()
            self.accept()
