"""MacroFlow 진입점.

실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다.
PyQt6 로드 실패 시 ctypes MessageBox로 오류 내용과 로그 경로를 알린다.

로그 위치: %LOCALAPPDATA%\\MacroFlow\\logs\\macroflow_YYYYMMDD_HHMMSS.log
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# ── 로그 디렉터리 / 파일 설정 ─────────────────────────────────────────────────
# PyQt6보다 먼저 설정해야 import 오류도 파일에 기록된다.

def _get_log_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    log_dir = base / "MacroFlow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _setup_logging() -> Path:
    """파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다."""
    log_dir = _get_log_dir()
    log_file = log_dir / f"macroflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return log_file


# ── ctypes 폴백 다이얼로그 ───────────────────────────────────────────────────
# PyQt6 없이도 오류 메시지를 화면에 표시할 수 있다.

def _fatal_dialog(title: str, message: str) -> None:
    """Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).

    Args:
        title: 다이얼로그 제목.
        message: 표시할 오류 메시지.
    """
    if sys.platform == "win32":
        import ctypes
        MB_ICONERROR = 0x10
        ctypes.windll.user32.MessageBoxW(0, message, title, MB_ICONERROR)  # type: ignore[attr-defined]


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    """애플리케이션 시작 진입점."""
    log_file = _setup_logging()
    logger = logging.getLogger(__name__)

    # ── 시작 환경 기록 ─────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("MacroFlow starting")
    logger.info(f"  log file   : {log_file}")
    logger.info(f"  python     : {sys.version}")
    logger.info(f"  executable : {sys.executable}")
    logger.info(f"  platform   : {sys.platform}")
    logger.info(f"  frozen     : {getattr(sys, 'frozen', False)}")
    logger.info(f"  cwd        : {Path.cwd()}")
    logger.info("=" * 60)

    # ── PyQt6 임포트 ───────────────────────────────────────────────────────
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import (
            QApplication,
            QLabel,
            QMainWindow,
            QStatusBar,
            QVBoxLayout,
            QWidget,
        )
        logger.info("PyQt6 import OK")
    except ImportError:
        msg = (
            f"PyQt6를 불러올 수 없습니다.\n\n"
            f"{traceback.format_exc()}\n"
            f"로그 파일:\n{log_file}"
        )
        logger.exception("PyQt6 import failed")
        _fatal_dialog("MacroFlow — 시작 오류", msg)
        sys.exit(1)
    except Exception:
        msg = (
            f"예기치 않은 오류:\n\n"
            f"{traceback.format_exc()}\n"
            f"로그 파일:\n{log_file}"
        )
        logger.exception("Unexpected error during import")
        _fatal_dialog("MacroFlow — 오류", msg)
        sys.exit(1)

    # ── QApplication + 메인 창 ─────────────────────────────────────────────
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MacroFlow")
        app.setApplicationVersion("0.1.0")
        logger.info("QApplication created")

        window = _build_placeholder_window(log_file, QMainWindow, QWidget,
                                            QVBoxLayout, QLabel, QStatusBar,
                                            Qt, QFont)
        window.show()
        logger.info("Main window shown")

        exit_code = app.exec()
        logger.info(f"App exited with code {exit_code}")
        sys.exit(exit_code)

    except Exception:
        msg = (
            f"UI 초기화 오류:\n\n"
            f"{traceback.format_exc()}\n"
            f"로그 파일:\n{log_file}"
        )
        logger.exception("UI initialization failed")
        _fatal_dialog("MacroFlow — UI 오류", msg)
        sys.exit(1)


def _build_placeholder_window(
    log_file: Path,
    QMainWindow: type,
    QWidget: type,
    QVBoxLayout: type,
    QLabel: type,
    QStatusBar: type,
    Qt: Any,
    QFont: type,
) -> Any:
    """M3 UI 구현 전 임시 플레이스홀더 창을 반환한다."""
    from macroflow import __version__

    window = QMainWindow()
    window.setWindowTitle(f"MacroFlow v{__version__}")
    window.setMinimumSize(480, 300)

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setSpacing(12)
    layout.setContentsMargins(32, 32, 32, 32)

    title_label = QLabel("MacroFlow")
    font = QFont()
    font.setPointSize(20)
    font.setBold(True)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]

    desc_label = QLabel(
        "Windows 매크로 녹화·재생 도구\n\n"
        "UI 개발 중입니다 (M3 예정).\n"
        "핵심 엔진(recorder / player / macro_file)은 준비되었습니다."
    )
    desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
    desc_label.setWordWrap(True)

    log_label = QLabel(f"로그: {log_file}")
    log_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # type: ignore[attr-defined]
    log_label.setWordWrap(True)
    log_font = QFont()
    log_font.setPointSize(8)
    log_label.setFont(log_font)

    layout.addStretch()
    layout.addWidget(title_label)
    layout.addWidget(desc_label)
    layout.addWidget(log_label)
    layout.addStretch()

    window.setCentralWidget(central)

    status_bar = QStatusBar()
    status_bar.showMessage("준비 완료 — F6: 녹화 시작/중지  |  F7: 재생 시작/중지  |  ESC×3: 긴급 중지")
    window.setStatusBar(status_bar)

    return window


if __name__ == "__main__":
    main()
