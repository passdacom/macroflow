"""MacroFlow 진입점.

PyQt6 QApplication을 초기화하고 MainWindow를 표시한다.
UI 레이어 (M3) 구현 전까지는 콘솔 메시지만 출력한다.
"""

from __future__ import annotations

import logging


def main() -> None:
    """애플리케이션 시작."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # TODO(M3): PyQt6 QApplication 초기화
    # from PyQt6.QtWidgets import QApplication
    # from macroflow.ui.main_window import MainWindow
    # app = QApplication(sys.argv)
    # window = MainWindow()
    # window.show()
    # sys.exit(app.exec())

    print("MacroFlow starting... (UI not yet implemented — see M3)")
    print("Core modules loaded. Run tests with: uv run pytest tests/ -v")


if __name__ == "__main__":
    main()
