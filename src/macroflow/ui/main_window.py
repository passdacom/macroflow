"""MacroFlow 메인 창.

전체 상태 머신(idle / recording / stopping / playing)을 관리한다.
F6/F7 글로벌 핫키(RegisterHotKey), 미니 오버레이, 이벤트 에디터를 통합한다.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path

from PyQt6.QtCore import QByteArray, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent, QKeySequence, QShowEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QTabWidget,
)

from macroflow.types import MacroData

from .editor import EventEditorWidget
from .overlay import OverlayWindow
from .sequencer import MacroSequencerWidget

logger = logging.getLogger(__name__)

# ── Win32 핫키 상수 ────────────────────────────────────────────────────────────
_HOTKEY_RECORD = 1
_HOTKEY_PLAY = 2
_VK_F6 = 0x75
_VK_F7 = 0x76
_WM_HOTKEY = 0x0312


# ── 메인 창 ───────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """MacroFlow 메인 창. 녹화·재생 상태 머신 + UI 통합."""

    # 워커 스레드 → 메인 스레드 신호
    _sig_recording_done = pyqtSignal(object)  # MacroData
    _sig_play_complete = pyqtSignal()
    _sig_play_error = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        # ── 상태 ──────────────────────────────────────────────────────────────
        # "idle" | "recording" | "stopping" | "playing"
        self._state: str = "idle"
        self._macro: MacroData | None = None
        self._current_file: Path | None = None
        self._hotkeys_registered: bool = False

        # ESC×3 감지 (앱 포커스 상태에서만)
        self._esc_times: deque[float] = deque(maxlen=3)

        # ── 하위 위젯 ─────────────────────────────────────────────────────────
        self._editor = EventEditorWidget()
        self._sequencer = MacroSequencerWidget()
        self._overlay = OverlayWindow()

        # ── UI 구성 ───────────────────────────────────────────────────────────
        self._setup_window()
        self._setup_menubar()
        self._setup_toolbar()

        tabs = QTabWidget()
        tabs.addTab(self._editor, "매크로 에디터")
        tabs.addTab(self._sequencer, "시퀀서")
        self.setCentralWidget(tabs)

        self._setup_statusbar()

        # ── 신호 연결 ─────────────────────────────────────────────────────────
        self._sig_recording_done.connect(self._on_recording_done)
        self._sig_play_complete.connect(self._on_play_complete)
        self._sig_play_error.connect(self._on_play_error)
        self._editor.macro_changed.connect(self._on_macro_changed)

        # ── 폴링 타이머 (250ms) ───────────────────────────────────────────────
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(250)
        self._poll_timer.timeout.connect(self._poll_state)

        self._update_toolbar()

    # ── 창 설정 ───────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        from macroflow import __version__
        self.setWindowTitle(f"MacroFlow v{__version__}")
        self.setMinimumSize(860, 520)
        self.resize(1000, 620)

    def _setup_menubar(self) -> None:
        mb = self.menuBar()

        # 파일 메뉴
        file_menu = mb.addMenu("파일(&F)")

        act_new = QAction("새 녹화 시작 (F6)", self)
        act_new.triggered.connect(self._toggle_recording)
        file_menu.addAction(act_new)

        file_menu.addSeparator()

        act_open = QAction("열기...  Ctrl+O", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._open_file)
        file_menu.addAction(act_open)

        act_save = QAction("저장  Ctrl+S", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_file)
        file_menu.addAction(act_save)

        act_save_as = QAction("다른 이름으로 저장...", self)
        act_save_as.triggered.connect(self._save_file_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_exit = QAction("종료", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # 도움말 메뉴
        help_menu = mb.addMenu("도움말(&H)")
        act_about = QAction("정보", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_toolbar(self) -> None:
        tb = self.addToolBar("메인 도구")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self._act_record = QAction("● 녹화", self)
        self._act_record.setToolTip("F6  —  녹화 시작/중지")
        self._act_record.setCheckable(True)
        self._act_record.triggered.connect(self._toggle_recording)
        tb.addAction(self._act_record)

        self._act_play = QAction("▶ 재생", self)
        self._act_play.setToolTip("F7  —  재생 시작/중지")
        self._act_play.triggered.connect(self._toggle_playback)
        tb.addAction(self._act_play)

        self._act_stop = QAction("⏹ 중지", self)
        self._act_stop.setToolTip("녹화 또는 재생을 즉시 중지합니다")
        self._act_stop.triggered.connect(self._emergency_stop)
        tb.addAction(self._act_stop)

        tb.addSeparator()

        # 재생 속도
        tb.addWidget(QLabel(" 속도:"))
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["0.5x", "1.0x", "2.0x", "5.0x"])
        self._speed_combo.setCurrentIndex(1)
        self._speed_combo.setToolTip("재생 속도 배율")
        self._speed_combo.setFixedWidth(64)
        tb.addWidget(self._speed_combo)

        # 반복 횟수
        tb.addWidget(QLabel("  반복:"))
        self._repeat_spin = QSpinBox()
        self._repeat_spin.setMinimum(1)
        self._repeat_spin.setMaximum(9999)
        self._repeat_spin.setValue(1)
        self._repeat_spin.setSuffix("회")
        self._repeat_spin.setToolTip("반복 재생 횟수")
        self._repeat_spin.setFixedWidth(72)
        tb.addWidget(self._repeat_spin)

        # 반복 간격
        tb.addWidget(QLabel("  간격:"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setMinimum(0)
        self._interval_spin.setMaximum(60000)
        self._interval_spin.setValue(500)
        self._interval_spin.setSuffix("ms")
        self._interval_spin.setToolTip("반복 재생 간 대기 시간 (ms)")
        self._interval_spin.setFixedWidth(80)
        tb.addWidget(self._interval_spin)

        tb.addSeparator()

        self._act_open = QAction("📂 열기", self)
        self._act_open.triggered.connect(self._open_file)
        tb.addAction(self._act_open)

        self._act_save = QAction("💾 저장", self)
        self._act_save.triggered.connect(self._save_file)
        tb.addAction(self._act_save)

    def _setup_statusbar(self) -> None:
        self._sb_state = QLabel("대기 중")
        self._sb_count = QLabel("")
        self._sb_hint = QLabel("F6: 녹화  |  F7: 재생  |  ESC×3: 긴급 중지")

        sb = self.statusBar()
        sb.addWidget(self._sb_state)
        sb.addWidget(QLabel("  |  "))
        sb.addWidget(self._sb_count)
        sb.addPermanentWidget(self._sb_hint)

    # ── 핫키 등록 (Windows) ───────────────────────────────────────────────────

    def showEvent(self, event: QShowEvent | None) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._hotkeys_registered:
            self._register_hotkeys()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        if self._state == "recording":
            self._do_stop_recording()
        elif self._state == "playing":
            from macroflow import player
            player.stop()
        if sys.platform == "win32" and self._hotkeys_registered:
            self._unregister_hotkeys()
        self._overlay.close()
        super().closeEvent(event)

    def _register_hotkeys(self) -> None:
        if sys.platform == "win32":
            import ctypes
            hwnd = int(self.winId())
            ok1 = bool(ctypes.windll.user32.RegisterHotKey(hwnd, _HOTKEY_RECORD, 0, _VK_F6))
            ok2 = bool(ctypes.windll.user32.RegisterHotKey(hwnd, _HOTKEY_PLAY, 0, _VK_F7))
            if ok1 and ok2:
                self._hotkeys_registered = True
                logger.info("글로벌 핫키 등록 완료: F6 (녹화), F7 (재생)")
            else:
                logger.warning("글로벌 핫키 등록 실패 — QShortcut 폴백 사용")
                self._register_shortcut_fallback()
        else:
            self._register_shortcut_fallback()

    def _register_shortcut_fallback(self) -> None:
        from PyQt6.QtWidgets import QShortcut
        QShortcut(QKeySequence("F6"), self).activated.connect(self._toggle_recording)
        QShortcut(QKeySequence("F7"), self).activated.connect(self._toggle_playback)
        logger.info("QShortcut 폴백 핫키 등록 (앱 포커스 상태에서만 작동)")

    def _unregister_hotkeys(self) -> None:
        import ctypes
        hwnd = int(self.winId())
        ctypes.windll.user32.UnregisterHotKey(hwnd, _HOTKEY_RECORD)
        ctypes.windll.user32.UnregisterHotKey(hwnd, _HOTKEY_PLAY)
        self._hotkeys_registered = False

    def nativeEvent(  # type: ignore[override]
        self,
        event_type: QByteArray | bytes | bytearray,
        message: object,
    ) -> tuple[bool, int]:
        """WM_HOTKEY 처리 (Windows 전용)."""
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            import ctypes
            import ctypes.wintypes
            msg = ctypes.wintypes.MSG.from_address(int(message))  # type: ignore[arg-type]
            if msg.message == _WM_HOTKEY:
                if msg.wParam == _HOTKEY_RECORD:
                    self._toggle_recording()
                    return True, 0
                if msg.wParam == _HOTKEY_PLAY:
                    self._toggle_playback()
                    return True, 0
        return False, 0

    # ── 상태 머신 ─────────────────────────────────────────────────────────────

    def _toggle_recording(self) -> None:
        if self._state == "idle":
            self._start_recording()
        elif self._state == "recording":
            self._do_stop_recording()

    def _start_recording(self) -> None:
        from macroflow import recorder
        recorder.start_recording()
        self._state = "recording"
        self._overlay.start_recording()
        self._poll_timer.start()
        self._update_toolbar()
        self._sb_state.setText("● 녹화 중")
        self._sb_count.setText("이벤트: 0")
        logger.info("녹화 시작")

    def _do_stop_recording(self) -> None:
        self._state = "stopping"
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("녹화 저장 중...")
        threading.Thread(
            target=self._stop_recording_worker, daemon=True, name="RecStopWorker"
        ).start()

    def _stop_recording_worker(self) -> None:
        from macroflow import recorder
        try:
            macro = recorder.stop_recording()
            self._auto_save_temp(macro)
            self._sig_recording_done.emit(macro)
        except Exception as exc:
            logger.exception("녹화 중지 오류")
            self._sig_play_error.emit(f"녹화 중지 오류: {exc}")

    def _on_recording_done(self, macro: object) -> None:
        assert isinstance(macro, MacroData)
        self._macro = macro
        self._state = "idle"
        self._overlay.stop()
        self._editor.load_macro(macro)
        self._update_toolbar()
        count = len(macro.events)
        self._sb_state.setText("대기 중")
        self._sb_count.setText(f"이벤트: {count}")
        logger.info(f"녹화 완료: {count}개 이벤트")

    def _toggle_playback(self) -> None:
        if self._state == "idle" and self._macro:
            self._start_playback()
        elif self._state == "playing":
            self._stop_playback()

    def _start_playback(self) -> None:
        if not self._macro:
            return

        speed_values = [0.5, 1.0, 2.0, 5.0]
        speed = speed_values[self._speed_combo.currentIndex()]
        repeat_count = self._repeat_spin.value()
        interval_ms = self._interval_spin.value()

        self._state = "playing"
        self._overlay.start_playing(speed)
        self._poll_timer.start()
        self._update_toolbar()
        self._sb_state.setText(f"▶ 재생 중 ({speed:.1f}x)")
        self._sb_count.setText(f"이벤트: {len(self._macro.events)}")
        logger.info(f"재생 시작 speed={speed} repeat={repeat_count} interval={interval_ms}ms")

        macro = self._macro

        def _repeat_worker() -> None:
            from macroflow import player
            for i in range(repeat_count):
                if player._stop_flag.is_set():  # type: ignore[attr-defined]
                    break

                done_event = threading.Event()
                error_holder: list[str] = []

                def _on_complete(_ev: threading.Event = done_event) -> None:
                    _ev.set()

                def _on_error(exc: Exception, _ev: threading.Event = done_event, _eh: list[str] = error_holder) -> None:
                    _eh.append(str(exc))
                    _ev.set()

                player.play(macro, speed=speed, on_complete=_on_complete, on_error=_on_error)

                # 재생 완료 대기
                while not done_event.is_set():
                    if player._stop_flag.is_set():  # type: ignore[attr-defined]
                        return
                    time.sleep(0.05)

                if error_holder:
                    self._sig_play_error.emit(error_holder[0])
                    return

                # 마지막 반복이 아니면 interval 대기
                if i < repeat_count - 1 and interval_ms > 0:
                    deadline = time.monotonic() + interval_ms / 1000.0
                    while time.monotonic() < deadline:
                        if player._stop_flag.is_set():  # type: ignore[attr-defined]
                            return
                        time.sleep(0.05)

            self._sig_play_complete.emit()

        threading.Thread(
            target=_repeat_worker, daemon=True, name="RepeatPlayWorker"
        ).start()

    def _stop_playback(self) -> None:
        from macroflow import player
        player.stop()
        self._state = "idle"
        self._overlay.stop()
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("재생 중지")
        logger.info("재생 중지")

    def _on_play_complete(self) -> None:
        self._state = "idle"
        self._overlay.stop()
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("재생 완료")
        logger.info("재생 완료")

    def _on_play_error(self, msg: str) -> None:
        self._state = "idle"
        self._overlay.stop()
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("재생 오류")
        QMessageBox.warning(self, "재생 오류", msg)
        logger.error(f"재생 오류: {msg}")

    def _emergency_stop(self) -> None:
        logger.info("긴급 중지")
        if self._state == "recording":
            self._do_stop_recording()
        elif self._state == "playing":
            self._stop_playback()

    # ── 폴링 타이머 ───────────────────────────────────────────────────────────

    def _poll_state(self) -> None:
        if self._state == "recording":
            from macroflow import recorder
            count = recorder.get_event_count()
            self._overlay.set_event_count(count)
            self._sb_count.setText(f"이벤트: {count}")
        elif self._state == "playing":
            from macroflow import player
            progress = player.get_progress()
            self._overlay.set_progress(progress)
            if not player.is_playing():
                self._on_play_complete()

    # ── UI 갱신 ───────────────────────────────────────────────────────────────

    def _update_toolbar(self) -> None:
        is_idle = self._state == "idle"
        is_rec = self._state == "recording"
        is_stop = self._state == "stopping"
        is_play = self._state == "playing"

        self._act_record.setEnabled(is_idle or is_rec)
        self._act_record.setChecked(is_rec)
        self._act_record.setText("■ 중지 (F6)" if is_rec else "● 녹화 (F6)")

        self._act_play.setEnabled(is_idle and self._macro is not None)
        self._act_play.setText("⏸ 일시정지 (F7)" if is_play else "▶ 재생 (F7)")

        self._act_stop.setEnabled(is_rec or is_play or is_stop)
        self._act_save.setEnabled(is_idle and self._macro is not None)

    # ── 파일 조작 ─────────────────────────────────────────────────────────────

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "매크로 파일 열기",
            str(Path.home()),
            "Macro JSON (*.json);;모든 파일 (*)",
        )
        if not path:
            return
        try:
            from macroflow import macro_file
            self._macro = macro_file.load(path)
            self._current_file = Path(path)
            self._editor.load_macro(self._macro)
            self._update_toolbar()
            self._sb_state.setText("파일 로드됨")
            self._sb_count.setText(f"이벤트: {len(self._macro.events)}")
            self.setWindowTitle(f"MacroFlow — {Path(path).name}")
            logger.info(f"파일 로드: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "파일 열기 오류", str(exc))
            logger.exception("파일 열기 오류")

    def _save_file(self) -> None:
        if not self._macro:
            return
        if self._current_file:
            self._do_save(str(self._current_file))
        else:
            self._save_file_as()

    def _save_file_as(self) -> None:
        if not self._macro:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "매크로 저장",
            str(Path.home()),
            "Macro JSON (*.json)",
        )
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"
        self._do_save(path)
        self._current_file = Path(path)
        self.setWindowTitle(f"MacroFlow — {Path(path).name}")

    def _do_save(self, path: str) -> None:
        if not self._macro:
            return
        from macroflow import macro_file
        macro_file.save(self._macro, path)
        self._sb_state.setText(f"저장 완료: {Path(path).name}")
        logger.info(f"저장: {path}")

    # ── 매크로 변경 콜백 ─────────────────────────────────────────────────────

    def _on_macro_changed(self, macro: object) -> None:
        if isinstance(macro, MacroData):
            self._macro = macro

    # ── 기타 ─────────────────────────────────────────────────────────────────

    def _auto_save_temp(self, macro: MacroData) -> None:
        from datetime import datetime

        from macroflow import macro_file
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path.home() / ".local" / "share"
        temp_dir = base / "MacroFlow" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = temp_dir / f"recording_{ts}.json"
        macro_file.save(macro, str(temp_file))
        logger.info(f"임시 저장: {temp_file}")

    def _show_about(self) -> None:
        from macroflow import __version__
        QMessageBox.about(
            self, "MacroFlow 정보",
            f"<b>MacroFlow v{__version__}</b><br><br>"
            "Windows 전용 마우스·키보드 매크로 녹화·재생 도구<br><br>"
            "F6: 녹화 시작/중지<br>"
            "F7: 재생 시작/중지<br>"
            "ESC×3: 긴급 중지",
        )

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """앱 포커스 상태에서 ESC×3 긴급 중지."""
        if event and event.key() == Qt.Key.Key_Escape:
            self._esc_times.append(time.monotonic())
            if (len(self._esc_times) == 3
                    and self._esc_times[-1] - self._esc_times[0] <= 0.5):
                self._emergency_stop()
                return
        super().keyPressEvent(event)
