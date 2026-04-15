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
import types
from datetime import datetime
from pathlib import Path

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
        ctypes.windll.user32.MessageBoxW(0, message, title, MB_ICONERROR)


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
        from PyQt6.QtWidgets import QApplication

        from macroflow.ui import MainWindow
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

    # ── 미처리 예외 훅 ────────────────────────────────────────────────────
    # Qt 슬롯 내 AttributeError 등 미처리 예외가 앱을 무음 종료시키는 것을 방지.
    # sys.excepthook 에 등록하면 Python 레벨 미처리 예외가 반드시 로그에 기록된다.
    def _excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: types.TracebackType | None,
    ) -> None:
        logger.critical(
            "미처리 예외 — 앱이 비정상 종료됩니다",
            exc_info=(exc_type, exc_value, exc_tb),
        )
        logging.shutdown()

    sys.excepthook = _excepthook

    # ── QApplication + 메인 창 ─────────────────────────────────────────────
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MacroFlow")
        app.setApplicationVersion("0.1.0")
        logger.info("QApplication created")

        window = MainWindow()
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


if __name__ == "__main__":
    main()
