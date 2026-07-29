"""MacroFlow 메인 창.

전체 상태 머신(idle / recording / stopping / playing)을 관리한다.
F6/F7/F8 글로벌 핫키(RegisterHotKey), 미니 오버레이, 이벤트 에디터를 통합한다.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, QSettings, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent, QKeySequence, QShowEvent
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
)

from macroflow.hotkey_config import (
    HotkeyConfig,
    arm_hotkey_config_recovery,
    disarm_hotkey_config_recovery,
    load_hotkey_config,
    save_hotkey_config,
)
from macroflow.types import MacroData
from macroflow.win32.hotkeys import (
    NativeHotkeySet,
    RegistrationResult,
    UnavailableHotkeyBackend,
    User32HotkeyBackend,
    registration_id_from_native_message,
)

from .editor import EventEditorWidget
from .favorites import FavoritesWidget
from .hotkey_runtime import HotkeyRuntime
from .hotkey_settings_dialog import HotkeySettingsDialog
from .hotkey_shortcuts import QtFocusedHotkeyBindings
from .overlay import OverlayWindow
from .playback_repeat import (
    PlaybackStartOptions,
    RepeatPlaybackSession,
    full_playback_options,
    range_playback_options,
)
from .quick_text_dialog import QuickTextDialog
from .quick_text_settings import (
    QUICK_TEXT_DELAY_KEY,
    quick_text_delay_input,
)
from .quick_text_settings import (
    quick_text_delay_override as _read_quick_text_delay_override,
)
from .sequencer import MacroSequencerWidget

logger = logging.getLogger(__name__)


def _set_quick_text_clipboard(text: str) -> bool:
    """Set only user-confirmed quick text without reading existing clipboard data."""
    from macroflow import win32

    return win32.set_clipboard_text(text)


def _quick_text_delay_override() -> int | None:
    """Return the app-level delay applied to newly recorded F9 text events."""
    from PyQt6.QtCore import QSettings

    return _read_quick_text_delay_override(QSettings("MacroFlow", "MacroFlow"))


def _configured_hotkey_label(window: object, action_id: str, default: str) -> str:
    config = getattr(window, "_hotkey_config", None)
    return config.binding_for(action_id) if isinstance(config, HotkeyConfig) else default


_MAX_RECENT_SAVES = 10
_CLOSE_WORKER_TIMEOUT_S = 3.0


# ── 메인 창 ───────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """MacroFlow 메인 창. 녹화·재생 상태 머신 + UI 통합."""

    # 워커 스레드 → 메인 스레드 신호
    _sig_recording_done = pyqtSignal(object)  # MacroData
    _sig_recording_save_warning = pyqtSignal(str)
    _sig_play_complete = pyqtSignal()
    _sig_play_error = pyqtSignal(str)
    _sig_emergency_stop = pyqtSignal()  # ESC×3 (LL Hook consumer → UI)
    _sig_play_event = pyqtSignal(int)   # 재생 중 이벤트 인덱스 알림
    _sig_repeat_cycle = pyqtSignal(int, int)  # current, total

    def __init__(self) -> None:
        super().__init__()

        # ── 상태 ──────────────────────────────────────────────────────────────
        # "idle" | "recording" | "stopping" | "playing"
        self._state: str = "idle"
        self._macro: MacroData | None = None
        self._current_file: Path | None = None
        self._hotkeys_registered: bool = False
        self._hotkey_config: HotkeyConfig = load_hotkey_config(
            QSettings("MacroFlow", "MacroFlow")
        )
        self._focused_hotkeys = QtFocusedHotkeyBindings(self)
        self._hotkey_runtime: HotkeyRuntime | None = None
        self._paused: bool = False
        self._quick_text_session_active: bool = False
        self._hotkey_settings_active: bool = False
        self._playback_pause_event = threading.Event()
        self._recording_stop_thread: threading.Thread | None = None

        # ESC×3 감지 (앱 포커스 상태에서만)
        self._esc_times: deque[float] = deque(maxlen=3)
        # 재생 속도 직접 입력 값
        self._custom_speed: float = 1.0
        # 이전 녹화 복원용 — 새 녹화 시작 직전에 저장
        self._prev_macro: MacroData | None = None
        # 이어서 녹화 상태 — stop 후 기존 매크로에 append할지 결정
        self._append_recording_mode: bool = False
        self._append_base_macro: MacroData | None = None
        # 반복 재생 세션 상태 — 긴급정지가 다음 cycle 시작까지 확실히 막도록 UI가 소유
        self._repeat_session: RepeatPlaybackSession | None = None

        # ── 하위 위젯 ─────────────────────────────────────────────────────────
        self._editor = EventEditorWidget()
        self._sequencer = MacroSequencerWidget()
        self._favorites = FavoritesWidget()
        self._overlay = OverlayWindow()

        # ── UI 구성 ───────────────────────────────────────────────────────────
        self._setup_window()
        self._setup_menubar()
        self._setup_toolbar()

        self._tabs = QTabWidget()
        self._tabs.addTab(self._editor, "매크로 에디터")
        self._tabs.addTab(self._sequencer, "시퀀서")
        self._tabs.addTab(self._favorites, "즐겨찾기")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self._tabs)

        # 즐겨찾기 디렉토리 설정
        self._favorites.set_favorites_dir(self._get_favorites_dir())

        self._setup_statusbar()

        # ── 신호 연결 ─────────────────────────────────────────────────────────
        self._sig_recording_done.connect(self._on_recording_done)
        self._sig_recording_save_warning.connect(self._on_recording_save_warning)
        self._sig_play_complete.connect(self._on_play_complete)
        self._sig_play_error.connect(self._on_play_error)
        self._sig_emergency_stop.connect(self._emergency_stop)
        self._sig_play_event.connect(self._editor.highlight_event)
        self._sig_repeat_cycle.connect(self._overlay.set_repeat)
        self._editor.macro_changed.connect(self._on_macro_changed)
        # 에디터 단일 이벤트 실행 요청
        self._editor.play_event_range.connect(self._on_play_event_range)
        # 시퀀서 더블클릭 → 매크로 에디터 탭으로 로드
        self._sequencer.open_in_editor.connect(self._load_file_and_switch_tab)
        # 시퀀서 병합 → 에디터 탭으로 전달
        self._sequencer.merge_to_editor.connect(self._on_merge_to_editor)
        self._sequencer.dirty_changed.connect(self._update_sequencer_tab_title)
        # 시퀀서 실행 완료/오류 시 emergency hook 해제 + 툴바 갱신
        self._sequencer.sequence_complete.connect(self._on_sequence_done)
        self._sequencer.sequence_error.connect(self._on_sequence_done)
        self._sequencer.sequence_progress.connect(self._overlay.set_flow_progress)
        # F6 캡처 힌트 오버레이 연동
        self._editor.f6_capture_started.connect(self._reject_f6_capture_if_busy)
        self._editor.f6_capture_started.connect(self._sequencer.cancel_f6_capture)
        self._editor.f6_capture_started.connect(self._show_f6_capture_hint)
        self._editor.f6_capture_ended.connect(self._overlay.stop_hint)
        self._sequencer.f6_capture_started.connect(self._reject_f6_capture_if_busy)
        self._sequencer.f6_capture_started.connect(self._editor.cancel_f6_capture)
        self._sequencer.f6_capture_started.connect(self._show_f6_capture_hint)
        self._sequencer.f6_capture_ended.connect(self._overlay.stop_hint)
        # 즐겨찾기 신호 연결
        self._favorites.open_in_editor.connect(self._load_file_and_switch_tab)
        self._favorites.add_to_sequencer.connect(self._add_favorite_to_sequencer)

        # ── 폴링 타이머 (250ms) ───────────────────────────────────────────────
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(250)
        self._poll_timer.timeout.connect(self._poll_state)

        self._update_toolbar()
        self._restore_settings()

    # ── 창 설정 ───────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        from macroflow import __version__
        self.setWindowTitle(f"MacroFlow v{__version__}")
        self.setMinimumSize(1180, 520)
        self.resize(1180, 620)

    def _setup_menubar(self) -> None:
        mb = self.menuBar()

        # 파일 메뉴
        file_menu = mb.addMenu("파일(&F)")

        self._act_new_record_menu = QAction("새 녹화 시작 (F6)", self)
        self._act_new_record_menu.triggered.connect(self._toggle_recording)
        file_menu.addAction(self._act_new_record_menu)

        self._act_append_record_menu = QAction("이어서 녹화...", self)
        self._act_append_record_menu.setToolTip("현재 매크로 뒤에 새로 녹화한 이벤트를 이어붙입니다")
        self._act_append_record_menu.triggered.connect(self._start_append_recording)
        file_menu.addAction(self._act_append_record_menu)

        file_menu.addSeparator()

        self._menu_open = QAction("매크로 열기...", self)
        self._menu_open.setShortcut(QKeySequence("Ctrl+O"))
        self._menu_open.triggered.connect(self._open_file)
        file_menu.addAction(self._menu_open)

        self._menu_save = QAction("매크로 저장", self)
        self._menu_save.setShortcut(QKeySequence("Ctrl+S"))
        self._menu_save.triggered.connect(self._save_file)
        file_menu.addAction(self._menu_save)

        self._menu_save_as = QAction("매크로 다른 이름으로 저장...", self)
        self._menu_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._menu_save_as.triggered.connect(self._save_file_as)
        file_menu.addAction(self._menu_save_as)

        file_menu.addSeparator()

        # 최근 녹화 서브메뉴
        self._recent_menu = QMenu("최근 녹화", self)
        file_menu.addMenu(self._recent_menu)
        self._refresh_recent_menu()

        file_menu.addSeparator()

        act_exit = QAction("종료", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # 설정 메뉴
        settings_menu = mb.addMenu("설정(&S)")
        self._act_hotkey_settings = QAction("단축키 설정...", self)
        self._act_hotkey_settings.setToolTip(
            "글로벌 운영 단축키와 매크로 에디터 동작 추가 단축키를 변경합니다"
        )
        self._act_hotkey_settings.triggered.connect(self._show_hotkey_settings)
        settings_menu.addAction(self._act_hotkey_settings)
        settings_menu.addSeparator()

        act_color_settings = QAction("색 체크 설정...", self)
        act_color_settings.setToolTip(
            "클릭 색 체크와 색 트리거 timeout/폴링 간격을 현재 매크로에 저장합니다"
        )
        act_color_settings.triggered.connect(self._show_color_check_settings)
        settings_menu.addAction(act_color_settings)

        self._act_quick_text_delay = QAction("F9 텍스트 재생 대기...", self)
        self._act_quick_text_delay.setToolTip(
            "녹화 중 F9로 삽입하는 텍스트 동작의 기본 재생 대기를 설정합니다"
        )
        self._act_quick_text_delay.triggered.connect(self._show_quick_text_delay_settings)
        settings_menu.addAction(self._act_quick_text_delay)

        # 도움말 메뉴
        help_menu = mb.addMenu("도움말(&H)")
        act_about = QAction("정보", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_toolbar(self) -> None:
        # ── 1행: 녹화 / 재생 / 중지 ──────────────────────────────────────────
        tb1 = self.addToolBar("제어")
        tb1.setObjectName("runtime-control-toolbar")
        tb1.setMovable(False)
        tb1.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._runtime_control_toolbar = tb1

        self._act_record = QAction("● 녹화 (F6)", self)
        self._act_record.setToolTip("F6  —  녹화 시작/중지")
        self._act_record.setCheckable(True)
        self._act_record.triggered.connect(self._toggle_recording)
        tb1.addAction(self._act_record)

        self._act_append_record = QAction("● 이어서 녹화", self)
        self._act_append_record.setToolTip("현재 매크로 끝에 새 녹화를 이어붙입니다")
        self._act_append_record.triggered.connect(self._start_append_recording)
        tb1.addAction(self._act_append_record)

        self._act_play = QAction("▶ 재생 (F7)", self)
        self._act_play.setToolTip("F7  —  재생 시작/중지")
        self._act_play.triggered.connect(self._toggle_playback)
        tb1.addAction(self._act_play)

        self._act_pause = QAction("⏸ 일시중지 (F8)", self)
        self._act_pause.setToolTip("F8  —  녹화/재생 일시중지 또는 계속")
        self._act_pause.triggered.connect(self._toggle_pause)
        tb1.addAction(self._act_pause)

        self._act_stop = QAction("⏹ 중지", self)
        self._act_stop.setToolTip("녹화 또는 재생을 즉시 중지합니다")
        self._act_stop.triggered.connect(self._emergency_stop)
        tb1.addAction(self._act_stop)

        self.addToolBarBreak()

        # ── 2행: 속도 / 반복 / 간격 / 구간 ──────────────────────────────────
        tb2 = self.addToolBar("재생 설정")
        tb2.setObjectName("playback-settings-toolbar")
        tb2.setMovable(False)
        self._playback_settings_toolbar = tb2

        tb2.addWidget(QLabel(" 속도:"))
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["0.5x", "1.0x", "2.0x", "3.0x", "4.0x", "5.0x", "직접 입력..."])
        self._speed_combo.setCurrentIndex(1)
        self._speed_combo.setToolTip("재생 속도 배율 (직접 입력 선택 시 수동 입력 가능)")
        self._speed_combo.setFixedWidth(95)
        self._speed_combo.currentIndexChanged.connect(self._on_speed_combo_changed)
        tb2.addWidget(self._speed_combo)

        tb2.addWidget(QLabel("  반복:"))
        self._repeat_spin = QSpinBox()
        self._repeat_spin.setMinimum(1)
        self._repeat_spin.setMaximum(9999)
        self._repeat_spin.setValue(1)
        self._repeat_spin.setSuffix("회")
        self._repeat_spin.setToolTip("반복 재생 횟수")
        self._repeat_spin.setFixedWidth(75)
        tb2.addWidget(self._repeat_spin)

        tb2.addWidget(QLabel("  반복 간격:"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setMinimum(0)
        self._interval_spin.setMaximum(60000)
        self._interval_spin.setValue(500)
        self._interval_spin.setSuffix("ms")
        self._interval_spin.setToolTip(
            "한 회 재생이 완전히 끝난 뒤 실제 시간으로 대기합니다. 재생 속도는 적용되지 않습니다."
        )
        self._interval_spin.setFixedWidth(85)
        tb2.addWidget(self._interval_spin)

        range_tb = self.addToolBar("구간 재생")
        range_tb.setObjectName("range-playback-toolbar")
        range_tb.setMovable(False)
        self._range_playback_toolbar = range_tb

        range_tb.addWidget(QLabel(" 구간:"))
        self._range_start_spin = QSpinBox()
        self._range_start_spin.setMinimum(0)
        self._range_start_spin.setMaximum(0)
        self._range_start_spin.setValue(0)
        self._range_start_spin.setSpecialValueText("처음")
        self._range_start_spin.setToolTip("구간 재생 시작 행 (0=처음부터)")
        self._range_start_spin.editingFinished.connect(self._normalize_range_spinboxes)
        self._range_start_spin.setFixedWidth(80)
        range_tb.addWidget(self._range_start_spin)

        range_tb.addWidget(QLabel("~"))
        self._range_end_spin = QSpinBox()
        self._range_end_spin.setMinimum(0)
        self._range_end_spin.setMaximum(0)
        self._range_end_spin.setValue(0)
        self._range_end_spin.setSpecialValueText("끝")
        self._range_end_spin.setToolTip("구간 재생 끝 행 (0=끝까지)")
        self._range_end_spin.editingFinished.connect(self._normalize_range_spinboxes)
        self._range_end_spin.setFixedWidth(80)
        range_tb.addWidget(self._range_end_spin)

        self._act_range_play = QAction("▶ 구간 재생", self)
        self._act_range_play.setToolTip("설정한 구간(시작~끝)만 재생합니다")
        self._act_range_play.triggered.connect(self._start_range_playback)
        range_tb.addAction(self._act_range_play)

        # 매크로 에디터 탭의 파일/내보내기 작업. 탭 내부의 고정 행에 배치한다.
        self._act_open = QAction("📂 열기", self)
        self._act_open.triggered.connect(self._open_file)

        self._act_save = QAction("💾 저장", self)
        self._act_save.setToolTip("현재 파일에 덮어쓰기 저장 (파일이 없으면 다른 이름으로 저장)")
        self._act_save.triggered.connect(self._save_file)

        self._act_save_as = QAction("💾 다른 이름", self)
        self._act_save_as.setToolTip("새 경로를 지정하여 저장")
        self._act_save_as.triggered.connect(self._save_file_as)

        self._act_save_seq = QAction("📋 시퀀서", self)
        self._act_save_seq.setToolTip("macros 폴더에 자동 저장 후 시퀀서에 추가")
        self._act_save_seq.triggered.connect(self._save_and_add_to_sequencer)

        self._act_save_fav = QAction("⭐ 즐겨찾기", self)
        self._act_save_fav.setToolTip(
            "현재 매크로를 이름을 지정하여 즐겨찾기로 저장합니다\n"
            "(favorites 폴더 — macros 폴더와 별도 보관)"
        )
        self._act_save_fav.triggered.connect(self._save_and_add_to_favorites)

        self._act_restore_prev = QAction("↩ 이전 복원", self)
        self._act_restore_prev.setToolTip(
            "새 녹화를 시작하기 직전의 매크로를 복원합니다\n"
            "(실수로 F6을 눌러 기존 매크로가 사라졌을 때 사용)"
        )
        self._act_restore_prev.triggered.connect(self._restore_prev_macro)
        self._act_restore_prev.setEnabled(False)

        self._editor.install_main_window_actions(
            document_actions=(self._act_open, self._act_save, self._act_save_as),
            export_actions=(
                self._act_save_seq,
                self._act_save_fav,
                self._act_restore_prev,
            ),
        )

    def _setup_statusbar(self) -> None:
        self._sb_state = QLabel("대기 중")
        self._sb_count = QLabel("")
        self._sb_hint = QLabel(
            "F6: 녹화  |  F7: 재생/색트리거  |  F8: 일시중지/계속  |  ESC×3: 긴급 중지"
        )

        sb = self.statusBar()
        sb.addWidget(self._sb_state)
        sb.addWidget(QLabel("  |  "))
        sb.addWidget(self._sb_count)
        sb.addPermanentWidget(self._sb_hint)

    # ── 핫키 등록 (Windows) ───────────────────────────────────────────────────

    def showEvent(self, event: QShowEvent | None) -> None:  # noqa: N802
        super().showEvent(event)
        if self._hotkey_runtime is None:
            self._initialize_hotkeys()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        if self._state in {"recording", "stopping"}:
            if not self._stop_recording_before_close():
                QMessageBox.warning(
                    self,
                    "녹화 종료 대기",
                    "녹화 저장 작업이 아직 종료되지 않았습니다. 잠시 후 다시 시도하세요.",
                )
                if event is not None:
                    event.ignore()
                return
        elif self._state == "playing":
            if not self._stop_playback():
                QMessageBox.warning(
                    self,
                    "재생 종료 대기",
                    "재생 worker가 아직 종료되지 않았습니다. 잠시 후 다시 시도하세요.",
                )
                if event is not None:
                    event.ignore()
                return
        if self._sequencer.is_running() and not self._stop_sequencer():
            QMessageBox.warning(
                self,
                "시퀀서 종료 대기",
                "시퀀서 실행이 아직 종료되지 않았습니다. 잠시 후 다시 시도하세요.",
            )
            if event is not None:
                event.ignore()
            return
        if not self._sequencer.confirm_discard_changes():
            if event is not None:
                event.ignore()
            return
        self._editor.cancel_f6_capture()
        self._sequencer.cancel_f6_capture()
        if self._hotkey_runtime is not None:
            shutdown = self._hotkey_runtime.shutdown()
            if not shutdown.success:
                logger.error("글로벌 단축키 해제 실패; 종료 전에 한 번 더 시도합니다")
                shutdown = self._hotkey_runtime.shutdown()
            if not shutdown.success:
                logger.critical("글로벌 단축키 해제를 완료하지 못했습니다")
            self._hotkey_runtime = None
            self._hotkeys_registered = False
        self._save_settings()
        self._overlay.close()
        super().closeEvent(event)

    def _save_settings(self) -> None:
        """창 위치·크기, 마지막 파일, 색 timeout 기본값을 QSettings에 저장한다."""
        from PyQt6.QtCore import QSettings
        s = QSettings("MacroFlow", "MacroFlow")
        s.setValue("geometry", self.saveGeometry())
        if self._current_file is not None:
            s.setValue("last_file", str(self._current_file))
        self._persist_color_settings(s)

    def _persist_color_settings(self, s: Any) -> None:
        """현재 매크로의 색 체크/트리거 설정을 앱 기본값으로 저장한다."""
        if self._macro is None:
            return
        settings = self._macro.settings
        # Legacy key도 함께 저장해 이전 버전 설정/파일과의 호환성을 유지한다.
        s.setValue("color_check_click_timeout_ms", settings.color_check_click_skip_timeout_ms)
        s.setValue("color_check_click_wait_timeout_ms", settings.color_check_click_wait_timeout_ms)
        s.setValue("color_check_click_skip_timeout_ms", settings.color_check_click_skip_timeout_ms)
        s.setValue("color_check_click_stop_timeout_ms", settings.color_check_click_stop_timeout_ms)
        s.setValue("color_check_click_interval_ms", settings.color_check_click_interval_ms)
        s.setValue("color_trigger_default_timeout_ms", settings.color_trigger_default_timeout_ms)
        s.setValue("color_trigger_check_interval_ms", settings.color_trigger_check_interval_ms)

    def _qsettings_int(self, s: Any, key: str, default: int) -> int:
        """QSettings 값 타입 차이를 안전하게 int로 정규화한다."""
        value = s.value(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _apply_persisted_color_settings(self, macro: MacroData) -> MacroData:
        """QSettings에 저장된 색 timeout 기본값을 MacroData에 반영한다."""
        from PyQt6.QtCore import QSettings
        s = QSettings("MacroFlow", "MacroFlow")
        settings = macro.settings

        def _timeout(key: str, default: int) -> int:
            return min(600000, max(0, self._qsettings_int(s, key, default)))

        def _interval(key: str, default: int) -> int:
            return min(10000, max(1, self._qsettings_int(s, key, default)))

        persisted_keys = (
            "color_check_click_timeout_ms",
            "color_check_click_wait_timeout_ms",
            "color_check_click_skip_timeout_ms",
            "color_check_click_stop_timeout_ms",
            "color_check_click_interval_ms",
            "color_trigger_default_timeout_ms",
            "color_trigger_check_interval_ms",
        )
        if all(s.value(key, None) is None for key in persisted_keys):
            return macro

        legacy_timeout = _timeout(
            "color_check_click_timeout_ms",
            settings.color_check_click_timeout_ms,
        )
        legacy_exists = s.value("color_check_click_timeout_ms", None) is not None
        per_action_default = legacy_timeout if legacy_exists else None
        wait_default = (
            per_action_default
            if per_action_default is not None
            else settings.color_check_click_wait_timeout_ms
        )
        skip_default = (
            per_action_default
            if per_action_default is not None
            else settings.color_check_click_skip_timeout_ms
        )
        stop_default = (
            per_action_default
            if per_action_default is not None
            else settings.color_check_click_stop_timeout_ms
        )
        new_settings = dataclasses.replace(
            settings,
            color_check_click_timeout_ms=legacy_timeout,
            color_check_click_wait_timeout_ms=_timeout(
                "color_check_click_wait_timeout_ms", wait_default
            ),
            color_check_click_skip_timeout_ms=_timeout(
                "color_check_click_skip_timeout_ms", skip_default
            ),
            color_check_click_stop_timeout_ms=_timeout(
                "color_check_click_stop_timeout_ms", stop_default
            ),
            color_check_click_interval_ms=_interval(
                "color_check_click_interval_ms", settings.color_check_click_interval_ms
            ),
            color_trigger_default_timeout_ms=_timeout(
                "color_trigger_default_timeout_ms", settings.color_trigger_default_timeout_ms
            ),
            color_trigger_check_interval_ms=_interval(
                "color_trigger_check_interval_ms", settings.color_trigger_check_interval_ms
            ),
        )
        return dataclasses.replace(macro, settings=new_settings)

    def _restore_settings(self) -> None:
        """QSettings에서 창 위치·크기와 마지막 파일을 복원한다."""
        from PyQt6.QtCore import QSettings
        s = QSettings("MacroFlow", "MacroFlow")
        geo = s.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        last_file = s.value("last_file", "")
        if last_file and Path(str(last_file)).exists():
            try:
                from macroflow.macro_file import load
                macro = load(str(last_file))
                macro = self._apply_persisted_color_settings(macro)
                self._macro = macro
                self._current_file = Path(str(last_file))
                self._editor.load_macro(macro)
                self._update_range_spinboxes()
                logger.info(f"마지막 파일 복원: {last_file}")
            except Exception as exc:
                logger.warning(f"마지막 파일 복원 실패 ({last_file}): {exc}")

    def _initialize_hotkeys(self) -> None:
        """Initialize native runtime hotkeys once and install focused fallbacks."""
        from macroflow import recorder

        backend = (
            User32HotkeyBackend(hwnd=int(self.winId()))
            if sys.platform == "win32"
            else UnavailableHotkeyBackend()
        )
        runtime = HotkeyRuntime(
            NativeHotkeySet(backend),
            self._focused_hotkeys,
            self._dispatch_hotkey_action,
        )
        result = runtime.initialize(self._hotkey_config)
        self._hotkey_runtime = runtime
        self._hotkeys_registered = result.success
        recorder.configure_filtered_hotkey_vk_codes(runtime.active_runtime_vks)
        if result.success:
            logger.info("글로벌 핫키 등록 완료: %s", dict(self._hotkey_config.bindings))
        elif sys.platform == "win32" and runtime.degraded:
            logger.error("글로벌 핫키 등록 정리가 불완전해 단축키를 비활성화했습니다")
            self._sb_state.setText(
                "글로벌 단축키 초기화가 불완전합니다. MacroFlow를 재시작하세요"
            )
        elif sys.platform == "win32":
            logger.warning(
                "글로벌 핫키 등록 실패 (%s: %s) — 앱 포커스 단축키 사용",
                result.failed_action_id,
                result.failed_key,
            )
            self._sb_state.setText(
                f"글로벌 단축키 {result.failed_key or ''} 충돌 — 설정에서 다른 키를 선택하세요"
            )
        self._refresh_hotkey_labels()
        self._on_tab_changed(self._tabs.currentIndex())

    def _dispatch_hotkey_action(self, action_id: str) -> None:
        """Route native and focused shortcuts through one logical command boundary."""
        if self._hotkey_settings_active:
            return
        if self._hotkey_runtime is not None and self._hotkey_runtime.degraded:
            self._sb_state.setText(
                "단축키 복구가 불완전합니다. 작업을 저장하고 MacroFlow를 재시작하세요"
            )
            return
        if action_id == "runtime.record_or_capture":
            self._handle_f6()
        elif action_id == "runtime.play_or_color_capture":
            if self._state == "recording":
                self._insert_color_trigger()
            else:
                self._toggle_playback()
        elif action_id == "runtime.pause_or_resume":
            self._toggle_pause()
        elif action_id == "recording.quick_text":
            self._capture_quick_text()
        elif action_id == "editor.insert_text":
            self._dispatch_editor_insert(self._editor.insert_text_action)
        elif action_id == "editor.insert_click":
            self._dispatch_editor_insert(self._editor.insert_click_action)
        elif action_id == "editor.insert_color_trigger":
            self._dispatch_editor_insert(self._editor.insert_color_trigger_action)
        else:
            logger.warning("알 수 없는 단축키 action: %s", action_id)

    def _dispatch_editor_insert(self, callback: Any) -> None:
        if (
            self._state == "idle"
            and not self._sequencer.is_running()
            and self._tabs.currentWidget() is self._editor
        ):
            callback()

    def _reject_f6_capture_if_busy(self) -> None:
        if self._state == "idle" and not self._sequencer.is_running():
            return
        self._editor.cancel_f6_capture()
        self._sequencer.cancel_f6_capture()
        self._sb_state.setText("녹화·재생·시퀀스 실행 중에는 위치를 캡처할 수 없습니다")

    def _show_f6_capture_hint(self) -> None:
        if self._state == "idle" and (
            self._editor.is_f6_capture_active()
            or self._sequencer.is_f6_capture_active()
        ):
            self._overlay.show_hint(
                f"{self._hotkey_label('runtime.record_or_capture')}을 눌러 위치 지정"
            )

    def _handle_f6(self) -> None:
        """Shared native/fallback F6 router with lifecycle-safe precedence."""
        if self._state in {"recording", "stopping"}:
            self._editor.cancel_f6_capture()
            self._sequencer.cancel_f6_capture()
            self._toggle_recording()
            return
        if self._state != "idle" or self._sequencer.is_running():
            self._reject_f6_capture_if_busy()
            return
        if (
            self._editor.is_f6_capture_active()
            or self._sequencer.is_f6_capture_active()
        ):
            self._do_f6_capture()
            return
        if not self._is_sequencer_tab() and not self._is_favorites_tab():
            self._toggle_recording()

    def nativeEvent(  # type: ignore[override]
        self,
        event_type: QByteArray | bytes | bytearray,
        message: object,
    ) -> tuple[bool, int]:
        """Dispatch WM_HOTKEY through the configured logical runtime."""
        registration_id = registration_id_from_native_message(event_type, message)
        if (
            registration_id is not None
            and self._hotkey_runtime is not None
            and self._hotkey_runtime.dispatch_native(registration_id)
        ):
            return True, 0
        return False, 0

    # ── 탭 관리 ──────────────────────────────────────────────────────────────

    def _is_sequencer_tab(self) -> bool:
        """현재 활성 탭이 시퀀서인지 반환한다."""
        return self._tabs.currentWidget() is self._sequencer

    def _is_favorites_tab(self) -> bool:
        """현재 활성 탭이 즐겨찾기인지 반환한다."""
        return self._tabs.currentWidget() is self._favorites

    def _update_sequencer_tab_title(self, dirty: bool) -> None:
        """시퀀서 탭에 미저장 변경 표시를 반영한다."""
        index = self._tabs.indexOf(self._sequencer)
        if index >= 0:
            self._tabs.setTabText(index, "시퀀서 *" if dirty else "시퀀서")

    def _on_tab_changed(self, _index: int) -> None:
        """탭 전환 시 툴바 버튼 상태와 상태바 힌트를 갱신한다."""
        if self._is_sequencer_tab():
            self._editor.cancel_f6_capture()
        elif self._tabs.currentWidget() is self._editor:
            self._sequencer.cancel_f6_capture()
        else:
            self._editor.cancel_f6_capture()
            self._sequencer.cancel_f6_capture()
        self._update_toolbar()
        record = self._hotkey_label("runtime.record_or_capture")
        play = self._hotkey_label("runtime.play_or_color_capture")
        pause = self._hotkey_label("runtime.pause_or_resume")
        quick_text = self._hotkey_label("recording.quick_text")
        if self._is_sequencer_tab():
            self._sb_hint.setText(f"{play}: 시퀀스 실행/중지  |  ESC×3: 긴급 중지")
        elif self._is_favorites_tab():
            self._sb_hint.setText("더블클릭: 매크로 로드  |  우클릭: 시퀀서 추가")
        else:
            self._sb_hint.setText(
                f"{record}: 녹화/캡처  |  {play}: 재생/색트리거  |  "
                f"{pause}: 일시중지  |  {quick_text}: 텍스트 기록  |  ESC×3"
            )

    # ── 상태 머신 ─────────────────────────────────────────────────────────────

    def _set_recording_paused_ui(self, paused: bool) -> None:
        self._paused = paused
        self._overlay.set_paused(paused)
        self._sb_state.setText(
            "Ⅱ 이어서 녹화 일시중지"
            if paused and self._append_recording_mode
            else "Ⅱ 녹화 일시중지"
            if paused
            else "● 이어서 녹화 중"
            if self._append_recording_mode
            else "● 녹화 중"
        )
        self._update_toolbar()

    def _capture_quick_text(self) -> None:
        """F9: composer 전체 구간을 제외하고 semantic text event를 기록·적용한다."""
        quick_text_key = _configured_hotkey_label(self, "recording.quick_text", "F9")
        if self._state != "recording":
            return
        if self._quick_text_session_active:
            self._sb_state.setText(f"{quick_text_key} 텍스트 입력이 이미 열려 있습니다")
            return
        from macroflow import recorder, win32

        self._quick_text_session_active = True
        owns_pause = False
        target_hwnd = 0
        restored = False
        focus_failure_warned = False
        try:
            owns_pause = not recorder.is_paused()
            if owns_pause and not recorder.pause_recording():
                return
            target_hwnd = win32.get_foreground_window()
            self._set_recording_paused_ui(True)

            dialog = QuickTextDialog(self, trigger_label=quick_text_key)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            text = dialog.text()
            if not text:
                self._sb_state.setText("빈 텍스트는 기록하지 않았습니다")
                return
            if len(text) > 100_000:
                QMessageBox.warning(
                    self,
                    "텍스트가 너무 깁니다",
                    "텍스트는 100,000자까지 기록할 수 있습니다.",
                )
                return

            restored = (
                target_hwnd > 0
                and win32.bring_window_to_foreground(target_hwnd)
                and win32.is_foreground_window(target_hwnd)
            )
            if not restored:
                focus_failure_warned = True
                QMessageBox.warning(
                    self,
                    "대상 창 복원 실패",
                    "원래 텍스트 입력 창을 확인할 수 없어 문구를 기록하지 않았습니다.",
                )
                return
            if not _set_quick_text_clipboard(text) or not win32.send_paste():
                QMessageBox.warning(
                    self,
                    "텍스트 입력 실패",
                    "대상 창에 텍스트를 모두 입력하지 못해 매크로에는 기록하지 않았습니다.",
                )
                return
            if not recorder.inject_text_input(
                text,
                delay_override_ms=_quick_text_delay_override(),
            ):
                QMessageBox.warning(
                    self,
                    "텍스트 기록 실패",
                    "대상 창에는 텍스트가 입력됐지만 매크로 기록에 실패했습니다.",
                )
                return
            self._sb_state.setText("텍스트 동작을 기록했습니다")
        finally:
            final_focus_restored = (
                target_hwnd > 0
                and win32.bring_window_to_foreground(target_hwnd)
                and win32.is_foreground_window(target_hwnd)
            )
            if (
                not final_focus_restored
                and not focus_failure_warned
                and self._state == "recording"
            ):
                QMessageBox.warning(
                    self,
                    "대상 창 복원 실패",
                    "원래 입력 창을 다시 확인할 수 없어 녹화를 일시중지 상태로 유지합니다.",
                )
            if (
                owns_pause
                and self._state == "recording"
                and final_focus_restored
            ):
                # Ctrl+Enter는 dialog를 Ctrl key-up보다 먼저 닫을 수 있다.
                # 재개 직후 도착하는 해당 release만 녹화되지 않도록 fence를 둔다.
                recorder.suppress_next_key_release({0x11, 0xA2, 0xA3})
                if recorder.resume_recording():
                    self._set_recording_paused_ui(False)
                else:
                    self._set_recording_paused_ui(True)
            elif owns_pause and self._state == "recording":
                self._set_recording_paused_ui(True)
            elif not owns_pause and self._state == "recording":
                self._set_recording_paused_ui(True)
            self._quick_text_session_active = False

    def _toggle_pause(self) -> None:
        """F8: 현재 녹화 또는 일반 재생을 일시중지/재개한다."""
        if self._state == "recording":
            if self._quick_text_session_active:
                quick_text_key = _configured_hotkey_label(
                    self, "recording.quick_text", "F9"
                )
                self._sb_state.setText(
                    f"{quick_text_key} 텍스트 입력 중에는 일시정지를 해제할 수 없습니다"
                )
                return
            from macroflow import recorder

            changed = (
                recorder.resume_recording()
                if self._paused
                else recorder.pause_recording()
            )
            if not changed:
                return
            self._set_recording_paused_ui(not self._paused)
            return
        elif self._state == "playing":
            from macroflow import player

            if self._paused:
                self._playback_pause_event.clear()
                player.resume()
                self._paused = False
            else:
                self._playback_pause_event.set()
                player.pause()
                self._paused = True
            self._overlay.set_paused(self._paused)
            self._sb_state.setText("Ⅱ 재생 일시중지" if self._paused else "▶ 재생 중")
        else:
            return
        self._update_toolbar()

    def _toggle_recording(self) -> None:
        if self._sequencer.is_running():
            self._sb_state.setText("시퀀스 실행 중에는 녹화할 수 없습니다")
            return
        if self._state == "idle":
            if self._tabs.currentWidget() is not self._editor:
                self._sb_state.setText("녹화는 매크로 에디터 탭에서 시작할 수 있습니다")
                return
            if (
                sys.platform == "win32"
                and self._hotkey_runtime is not None
                and not self._hotkey_runtime.globally_registered
            ):
                self._sb_state.setText(
                    "녹화 전에 설정에서 사용 가능한 글로벌 단축키를 선택하세요"
                )
                return
            self._start_recording()
        elif self._state in {"recording", "stopping"}:
            self._do_stop_recording()

    def _start_append_recording(self) -> None:
        """현재 매크로 뒤에 새 녹화를 이어붙이는 녹화 모드를 시작한다."""
        if self._state != "idle" or self._sequencer.is_running() or self._macro is None:
            return
        reply = QMessageBox.question(
            self,
            "이어서 녹화",
            "현재 매크로 끝에 새 녹화를 이어붙입니다.\n\n"
            f"{self._hotkey_label('runtime.record_or_capture')} 또는 중지 버튼으로 "
            "녹화를 끝내면 새 이벤트가 뒤에 추가됩니다.\n"
            "계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._append_recording_mode = True
        self._append_base_macro = copy.deepcopy(self._macro)
        self._start_recording()

    def _start_recording(self) -> None:
        # 기존 매크로가 있으면 복원을 위해 백업한다 (실수로 F6 눌렀을 때 복원 가능)
        if self._macro is not None:
            self._prev_macro = copy.deepcopy(self._macro)
            self._auto_save_prev_recording(self._prev_macro)
            logger.info("이전 매크로 백업 완료 (복원 버튼으로 되돌릴 수 있음)")

        from macroflow import recorder
        try:
            recorder.start_recording(on_emergency_stop=self._sig_emergency_stop.emit)
        except Exception as exc:
            self._append_recording_mode = False
            self._append_base_macro = None
            logger.exception("녹화 시작 오류")
            QMessageBox.critical(self, "녹화 시작 오류", f"녹화를 시작할 수 없습니다.\n\n{exc}")
            return
        self._paused = False
        self._state = "recording"
        self._overlay.start_recording()
        self._poll_timer.start()
        self._update_toolbar()
        if self._append_recording_mode:
            self._sb_state.setText("● 이어서 녹화 중")
            logger.info("이어서 녹화 시작")
        else:
            self._sb_state.setText("● 녹화 중")
            logger.info("녹화 시작")
        self._sb_count.setText("이벤트: 0")

    def _do_stop_recording(self) -> None:
        if (
            self._recording_stop_thread is not None
            and self._recording_stop_thread.is_alive()
        ):
            return
        self._paused = False
        self._state = "stopping"
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("녹화 저장 중...")
        self._recording_stop_thread = threading.Thread(
            target=self._stop_recording_worker,
            daemon=True,
            name="RecStopWorker",
        )
        self._recording_stop_thread.start()

    def _stop_recording_before_close(self) -> bool:
        """녹화 저장 worker 완료를 기다리고 완료 signal까지 UI에 반영한다."""
        if self._state == "recording":
            self._do_stop_recording()
        worker = self._recording_stop_thread
        if worker is None:
            return self._state == "idle"
        worker.join(timeout=_CLOSE_WORKER_TIMEOUT_S)
        if worker.is_alive():
            return False
        QApplication.processEvents()
        return self._state == "idle"

    def _stop_recording_worker(self) -> None:
        from macroflow import recorder
        try:
            macro = recorder.stop_recording()
        except Exception as exc:
            logger.exception("녹화 중지 오류")
            self._sig_play_error.emit(f"녹화 중지 오류: {exc}")
            return
        warning: str | None = None
        try:
            self._auto_save_temp(macro)
        except Exception as exc:
            logger.exception("최근 녹화 임시 저장 오류")
            warning = f"녹화 내용은 에디터에 보존했지만 최근 녹화 임시 저장에 실패했습니다: {exc}"
        self._sig_recording_done.emit(macro)
        if warning is not None:
            self._sig_recording_save_warning.emit(warning)

    def _on_recording_done(self, macro: object) -> None:
        self._recording_stop_thread = None
        assert isinstance(macro, MacroData)
        macro = self._apply_persisted_color_settings(macro)
        if self._append_recording_mode and self._append_base_macro is not None:
            from macroflow.ui.append_recording import append_recording

            appended_macro = append_recording(self._append_base_macro, macro)
            appended_macro = self._apply_persisted_color_settings(appended_macro)
            self._macro = appended_macro
            self._append_recording_mode = False
            self._append_base_macro = None
            self._state = "idle"
            self._overlay.stop()
            self._editor.load_macro(appended_macro)
            self._update_toolbar()
            self._update_range_spinboxes()
            count = len(appended_macro.events)
            added_count = len(macro.events)
            self._sb_state.setText("이어서 녹화 완료")
            self._sb_count.setText(f"이벤트: {count} (+{added_count})")
            self._refresh_recent_menu()
            logger.info(f"이어서 녹화 완료: {added_count}개 추가, 총 {count}개 이벤트")
            return

        self._append_recording_mode = False
        self._append_base_macro = None
        self._macro = macro
        self._state = "idle"
        self._overlay.stop()
        self._editor.load_macro(macro)
        self._update_toolbar()
        self._update_range_spinboxes()
        count = len(macro.events)
        self._sb_state.setText("대기 중")
        self._sb_count.setText(f"이벤트: {count}")
        self._refresh_recent_menu()
        logger.info(f"녹화 완료: {count}개 이벤트")

    def _on_recording_save_warning(self, message: str) -> None:
        QMessageBox.warning(self, "최근 녹화 저장 오류", message)
        logger.warning(message)

    def _stop_sequencer(self) -> bool:
        """시퀀서 worker와 관련 overlay/hook/UI 상태를 함께 정리한다."""
        stopped = self._sequencer.stop_sequence()
        self._overlay.stop()
        if sys.platform == "win32":
            from macroflow.win32 import stop_emergency_hook
            stop_emergency_hook()
        self._update_toolbar()
        self._sb_state.setText(
            "시퀀스 중지" if stopped else "시퀀스 중지 요청됨 — worker 종료 대기 중"
        )
        return stopped

    def _toggle_sequencer(self) -> None:
        """시퀀서 탭에서 F7: 시퀀스 실행 중이면 중지, 아니면 실행."""
        if self._sequencer.is_running():
            self._stop_sequencer()
        elif self._state != "idle":
            self._sb_state.setText("녹화/재생 중에는 시퀀스를 시작할 수 없습니다")
        elif self._sequencer.has_items():
            if sys.platform == "win32":
                from macroflow.win32 import start_emergency_hook
                try:
                    start_emergency_hook(self._sig_emergency_stop.emit)
                except Exception as exc:
                    logger.exception("시퀀스 긴급 중지 Hook 시작 오류")
                    self._sb_state.setText(f"시퀀스 시작 오류: 긴급 중지 Hook 실패 ({exc})")
                    QMessageBox.warning(
                        self,
                        "시퀀스 시작 오류",
                        f"긴급 중지 Hook을 시작하지 못해 실행을 취소했습니다.\n\n{exc}",
                    )
                    return
            speed_presets = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
            idx = self._speed_combo.currentIndex()
            speed = self._custom_speed if idx == 6 else speed_presets[idx]
            self._overlay.start_flowing(
                speed,
                current=1,
                total=self._sequencer.item_count(),
            )
            try:
                started = self._sequencer.run_sequence(speed=speed)
            except Exception as exc:
                self._overlay.stop()
                if sys.platform == "win32":
                    from macroflow.win32 import stop_emergency_hook
                    stop_emergency_hook()
                self._sb_state.setText(f"시퀀스 시작 오류: {exc}")
                logger.exception("시퀀스 시작 오류")
                return
            if started is False:
                self._overlay.stop()
                if sys.platform == "win32":
                    from macroflow.win32 import stop_emergency_hook

                    stop_emergency_hook()
                self._update_toolbar()
                return
            self._update_toolbar()
            self._sb_state.setText(f"▶ 시퀀스 실행 중 ({speed:.1f}x)")

    def _toggle_playback(self) -> None:
        if self._state == "playing":
            self._stop_playback()
            return
        # 시퀀서 탭에서는 단일 매크로 재생 대신 시퀀스 실행/중지로 위임
        # (RegisterHotKey 폴백 QShortcut 경로에서도 일관된 동작 보장)
        if self._is_sequencer_tab():
            self._toggle_sequencer()
            return
        if self._is_favorites_tab():
            return
        if self._sequencer.is_running():
            self._sb_state.setText("시퀀스 실행 중에는 일반 재생을 시작할 수 없습니다")
            return
        if self._state == "idle" and self._macro:
            self._start_playback()

    def _bring_to_front_for_prompt(self) -> None:
        """사용자 확인창을 띄우기 전에 메인 창을 전면으로 복원한다."""
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()
        if sys.platform == "win32":
            from macroflow.win32 import bring_window_to_foreground

            bring_window_to_foreground(int(self.winId()))

    def _start_playback(
        self,
        options: PlaybackStartOptions | None = None,
        forced_range: tuple[int, int] | None = None,
    ) -> None:
        if not self._macro:
            return

        _speed_presets = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
        idx = self._speed_combo.currentIndex()
        speed = self._custom_speed if idx == 6 else _speed_presets[idx]
        if options is None:
            if forced_range is not None:
                options = range_playback_options(forced_range)
            else:
                options = full_playback_options(self._repeat_spin.value())
        repeat_count = options.repeat_count
        interval_ms = self._interval_spin.value()

        if options.confirm_repeat and repeat_count > 1:
            self._bring_to_front_for_prompt()
            reply = QMessageBox.question(
                self,
                "반복 재생",
                f"{repeat_count:02d}회 반복 재생 하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 일반 재생은 항상 전체 재생(None). 구간 재생 버튼/단일 이벤트 실행만 event_range를 전달한다.
        event_range = options.event_range

        # 긴급 중지 Hook을 먼저 확보한다. 실패한 상태로 재생을 시작하면 사용자가
        # 입력을 중단할 안전장치가 없으므로 UI state를 바꾸지 않고 종료한다.
        try:
            from macroflow.win32 import start_emergency_hook
            start_emergency_hook(self._sig_emergency_stop.emit)
        except Exception as exc:
            logger.exception("긴급 중지 Hook 시작 오류")
            self._sb_state.setText(f"재생 시작 오류: 긴급 중지 Hook 실패 ({exc})")
            QMessageBox.warning(
                self,
                "재생 시작 오류",
                f"긴급 중지 Hook을 시작하지 못해 재생을 취소했습니다.\n\n{exc}",
            )
            return

        self._state = "playing"
        self._paused = False
        self._playback_pause_event.clear()
        self._repeat_session = RepeatPlaybackSession(total=repeat_count)
        self._repeat_session.mark_started()
        self._overlay.start_playing(speed, repeat_current=1, repeat_total=repeat_count)
        self._poll_timer.start()
        self._update_toolbar()

        range_str = ""
        if event_range is not None:
            range_str = f" [구간 {self._range_start_spin.value()}~{self._range_end_spin.value()}]"
        self._sb_state.setText(f"▶ 재생 중 ({speed:.1f}x){range_str}")
        self._sb_count.setText(f"이벤트: {len(self._macro.events)}")
        logger.info(
            f"재생 시작 speed={speed} repeat={repeat_count} "
            f"interval={interval_ms}ms range={event_range}"
        )

        macro = self._macro

        def _on_event(idx: int, _event: object) -> None:
            self._sig_play_event.emit(idx)

        def _repeat_worker(
            _range: tuple[int, int] | None = event_range,
        ) -> None:
            from macroflow import player
            for i in range(repeat_count):
                session = self._repeat_session
                if session is None or not session.should_start_cycle(i):
                    break
                while self._playback_pause_event.is_set():
                    session = self._repeat_session
                    if session is None or session.was_stopped:
                        return
                    time.sleep(0.02)
                session.mark_cycle_started(i)
                self._sig_repeat_cycle.emit(i + 1, repeat_count)

                done_event = threading.Event()
                error_holder: list[str] = []

                def _on_complete(_ev: threading.Event = done_event) -> None:
                    _ev.set()

                def _on_error(exc: Exception, _ev: threading.Event = done_event, _eh: list[str] = error_holder) -> None:
                    _eh.append(str(exc))
                    _ev.set()

                try:
                    player.play(
                        macro,
                        speed=speed,
                        on_event_start=_on_event,
                        on_complete=_on_complete,
                        on_error=_on_error,
                        event_range=_range,
                        start_pause_requested=self._playback_pause_event.is_set,
                    )
                except Exception as exc:
                    self._sig_play_error.emit(str(exc))
                    return

                # 재생 완료 대기
                while not done_event.is_set():
                    session = self._repeat_session
                    if session is None or session.was_stopped:
                        return
                    time.sleep(0.05)

                if error_holder:
                    self._sig_play_error.emit(error_holder[0])
                    return

                # 마지막 반복이 아니면 interval 대기
                if i < repeat_count - 1 and interval_ms > 0:
                    session = self._repeat_session
                    if session is not None:
                        session.mark_between_cycles()
                    remaining_s = interval_ms / 1000.0
                    last_active = time.monotonic()
                    while remaining_s > 0:
                        session = self._repeat_session
                        if session is None or session.was_stopped:
                            return
                        now = time.monotonic()
                        if self._playback_pause_event.is_set():
                            last_active = now
                            time.sleep(0.02)
                            continue
                        remaining_s -= now - last_active
                        last_active = now
                        time.sleep(min(0.05, max(0.0, remaining_s)))

            session = self._repeat_session
            if session is not None:
                session.mark_finished()
            self._sig_play_complete.emit()

        threading.Thread(
            target=_repeat_worker, daemon=True, name="RepeatPlayWorker"
        ).start()

    def _normalize_range_spinboxes(self) -> None:
        """빈 구간 입력을 0 sentinel로 되돌려 '처음'/'끝' 표시를 복원한다."""
        for spin in (self._range_start_spin, self._range_end_spin):
            if not spin.text().strip():
                spin.setValue(0)

    def _calc_event_range(self) -> tuple[int, int] | None:
        """구간 SpinBox 값에서 event_range (start, end exclusive)를 계산한다."""
        start_row = self._range_start_spin.value()
        end_row = self._range_end_spin.value()
        if start_row == 0 and end_row == 0:
            return None  # 전체 재생
        total = self._editor.row_count()
        if total == 0:
            return None
        effective_start = start_row if start_row > 0 else 1
        effective_end = end_row if end_row > 0 else total
        return self._editor.get_event_range_for_rows(effective_start, effective_end)

    def _stop_playback(self) -> bool:
        from macroflow import player
        from macroflow.win32 import stop_emergency_hook
        if self._repeat_session is not None:
            self._repeat_session.request_stop()
        self._playback_pause_event.clear()
        self._paused = False
        player.stop()
        stop_emergency_hook()
        stopped = not player.is_playing()
        self._overlay.stop()
        if not stopped:
            self._sb_state.setText("재생 중지 요청됨 — worker 종료 대기 중")
            self._update_toolbar()
            return False
        if self._repeat_session is not None:
            self._repeat_session.mark_finished()
        self._repeat_session = None
        self._state = "idle"
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("재생 중지")
        logger.info("재생 중지")
        return True

    def _on_play_complete(self) -> None:
        from macroflow.win32 import stop_emergency_hook
        stop_emergency_hook()
        if self._repeat_session is not None:
            self._repeat_session.mark_finished()
        self._repeat_session = None
        self._playback_pause_event.clear()
        self._paused = False
        self._state = "idle"
        self._overlay.stop()
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("재생 완료")
        logger.info("재생 완료")

    def _on_play_error(self, msg: str) -> None:
        if self._state == "stopping":
            self._recording_stop_thread = None
            from macroflow import recorder
            if recorder.is_recording():
                self._update_toolbar()
                self._sb_state.setText("녹화 중지 오류 — 중지 버튼으로 다시 시도하세요")
                QMessageBox.warning(self, "녹화 중지 오류", msg)
                logger.error(f"녹화 중지 오류: {msg}")
                return
        from macroflow.win32 import stop_emergency_hook
        stop_emergency_hook()
        if self._repeat_session is not None:
            self._repeat_session.mark_finished()
        self._repeat_session = None
        self._playback_pause_event.clear()
        self._paused = False
        self._state = "idle"
        self._overlay.stop()
        self._poll_timer.stop()
        self._update_toolbar()
        self._sb_state.setText("재생 오류")
        QMessageBox.warning(self, "재생 오류", msg)
        logger.error(f"재생 오류: {msg}")

    def _do_f6_capture(self) -> None:
        """F6 캡처 모드: 현재 마우스 위치와 픽셀 색을 에디터 캡처 콜백으로 전달한다."""
        if sys.platform != "win32":
            return
        from macroflow.win32 import get_cursor_pos, get_pixel_color, pixel_to_ratio

        x, y = get_cursor_pos()
        x_r, y_r = pixel_to_ratio(x, y)
        r, g, b = get_pixel_color(x, y)
        color_hex = f"#{r:02X}{g:02X}{b:02X}"

        if self._sequencer.is_f6_capture_active():
            self._sequencer.consume_f6_capture(x_r, y_r, color_hex)
        else:
            self._editor.consume_f6_capture(x_r, y_r, color_hex)
        self._overlay.stop_hint()
        logger.info(f"F6 캡처: ({x_r:.3f}, {y_r:.3f}) {color_hex}")

    def _insert_color_trigger(self) -> None:
        """녹화 중 F7: 현재 마우스 커서 위치의 픽셀 색을 ColorTriggerEvent로 삽입한다."""
        if self._paused:
            self._sb_state.setText("Ⅱ 녹화 일시중지 중에는 색상 체크를 삽입할 수 없습니다")
            return
        from macroflow import recorder
        from macroflow.win32 import get_cursor_pos, get_pixel_color, pixel_to_ratio

        x, y = get_cursor_pos()
        r, g, b = get_pixel_color(x, y)
        color_hex = f"#{r:02X}{g:02X}{b:02X}"
        x_ratio, y_ratio = pixel_to_ratio(x, y)

        timeout_ms = 0
        check_interval_ms = 50
        if self._macro is not None:
            timeout_ms = self._macro.settings.color_trigger_default_timeout_ms
            check_interval_ms = self._macro.settings.color_trigger_check_interval_ms

        recorder.inject_color_trigger(
            x_ratio,
            y_ratio,
            color_hex,
            timeout_ms=timeout_ms,
            check_interval_ms=check_interval_ms,
        )

        self._sb_state.setText(f"● 녹화 중  |  색상 체크 삽입: {color_hex}  ({x}, {y})")
        logger.info(f"색상 체크 삽입: {color_hex} @ pixel ({x}, {y})")

    def _show_hotkey_settings(self) -> None:
        """Validate, transactionally register, then persist a new hotkey set."""
        if self._hotkey_change_blocked():
            QMessageBox.information(
                self,
                "단축키 변경 불가",
                "녹화·재생·시퀀스 실행·위치 캡처가 모두 끝난 뒤 변경해 주세요.",
            )
            return
        if self._hotkey_runtime is None:
            QMessageBox.warning(self, "단축키 오류", "단축키 시스템이 아직 초기화되지 않았습니다.")
            return

        dialog = HotkeySettingsDialog(self._hotkey_config, self)
        self._hotkey_settings_active = True
        try:
            accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally:
            self._hotkey_settings_active = False
        if not accepted:
            return
        if self._hotkey_change_blocked():
            QMessageBox.information(
                self,
                "단축키 변경 취소",
                "설정 중 앱 상태가 변경되어 단축키를 적용하지 않았습니다.",
            )
            return
        candidate = dialog.candidate_config()
        result = self._apply_hotkey_config(candidate)
        if not result.success:
            if result.failed_key == "설정 저장":
                title = "단축키 설정 저장 실패"
                detail = "설정 파일에 저장하지 못해 이전 단축키 설정으로 되돌렸습니다."
            else:
                title = "글로벌 단축키 충돌"
                detail = (
                    f"{result.failed_key or '선택한 키'}는 다른 프로그램에서 사용 중이거나 "
                    "Windows에 등록할 수 없습니다. 기존 단축키 설정을 유지합니다."
                )
            if not result.rollback_succeeded:
                detail += (
                    "\n\n기존 단축키 또는 설정 파일 복구도 완료되지 않았습니다. "
                    "자동화 명령을 비활성화했습니다. 앱을 재시작해 주세요."
                )
            QMessageBox.warning(self, title, detail)
            self._hotkeys_registered = self._hotkey_runtime.globally_registered
            return

        self._sb_state.setText("단축키 설정을 적용했습니다")

    def _apply_hotkey_config(self, candidate: HotkeyConfig) -> RegistrationResult:
        """Apply atomically; persist and update recorder only after registration succeeds."""
        if self._hotkey_change_blocked():
            return RegistrationResult(
                success=False,
                failed_key="앱 사용 중",
                rollback_succeeded=True,
            )
        if self._hotkey_runtime is None:
            return RegistrationResult(success=False, rollback_succeeded=True)
        settings = QSettings("MacroFlow", "MacroFlow")
        old_config = self._hotkey_config
        if not arm_hotkey_config_recovery(settings, old_config):
            return RegistrationResult(
                success=False,
                failed_key="설정 복구 준비",
                rollback_succeeded=True,
            )
        result = self._hotkey_runtime.apply(candidate)
        self._hotkeys_registered = self._hotkey_runtime.globally_registered
        if not result.success:
            disarm_hotkey_config_recovery(settings)
            if self._hotkey_runtime.degraded:
                self._update_toolbar()
            return result

        from macroflow import recorder

        candidate_persisted = save_hotkey_config(settings, candidate)
        recovery_disarmed = (
            candidate_persisted and disarm_hotkey_config_recovery(settings)
        )
        if not candidate_persisted or not recovery_disarmed:
            rollback = self._hotkey_runtime.apply(old_config)
            self._hotkeys_registered = self._hotkey_runtime.globally_registered
            old_persisted = save_hotkey_config(settings, old_config)
            recovery_cleared = old_persisted and disarm_hotkey_config_recovery(settings)
            rollback_succeeded = rollback.success and old_persisted and recovery_cleared
            if not rollback_succeeded:
                self._hotkey_runtime.degraded = True
            self._update_toolbar()
            return RegistrationResult(
                success=False,
                failed_key="설정 저장",
                rollback_succeeded=rollback_succeeded,
            )
        self._hotkey_config = candidate
        recorder.configure_filtered_hotkey_vk_codes(self._hotkey_runtime.active_runtime_vks)
        self._refresh_hotkey_labels()
        self._update_toolbar()
        self._on_tab_changed(self._tabs.currentIndex())
        return result

    def _hotkey_change_blocked(self) -> bool:
        return (
            self._state != "idle"
            or self._sequencer.is_running()
            or self._quick_text_session_active
            or self._editor.is_f6_capture_active()
            or self._sequencer.is_f6_capture_active()
        )

    def _hotkey_label(self, action_id: str) -> str:
        return self._hotkey_config.binding_for(action_id)

    def _refresh_hotkey_labels(self) -> None:
        record = self._hotkey_label("runtime.record_or_capture")
        play = self._hotkey_label("runtime.play_or_color_capture")
        pause = self._hotkey_label("runtime.pause_or_resume")
        quick_text = self._hotkey_label("recording.quick_text")
        self._act_record.setToolTip(f"{record}  —  녹화 시작/중지 또는 위치 캡처")
        self._act_play.setToolTip(f"{play}  —  재생/시퀀스 시작·중지 또는 색상 캡처")
        self._act_pause.setToolTip(f"{pause}  —  녹화/재생 일시정지 또는 계속")
        self._editor.set_capture_hotkey_label(record)
        self._editor.set_insertion_shortcut_labels(
            self._hotkey_label("editor.insert_text"),
            self._hotkey_label("editor.insert_click"),
            self._hotkey_label("editor.insert_color_trigger"),
        )
        self._sequencer.set_capture_hotkey_label(record)
        self._act_new_record_menu.setText(f"새 녹화 시작 ({record})")
        self._act_restore_prev.setToolTip(
            "새 녹화를 시작하기 직전의 매크로를 복원합니다\n"
            f"(실수로 {record}을 눌러 기존 매크로가 사라졌을 때 사용)"
        )
        self._act_quick_text_delay.setText(f"{quick_text} 텍스트 재생 대기...")
        self._act_quick_text_delay.setToolTip(
            f"녹화 중 {quick_text}로 삽입하는 텍스트 동작의 기본 재생 대기를 설정합니다"
        )

    def _show_quick_text_delay_settings(self) -> None:
        """새 F9 TextInputEvent에 적용할 앱 공통 재생 대기 기본값을 편집한다."""
        from PyQt6.QtCore import QSettings

        quick_text_key = _configured_hotkey_label(self, "recording.quick_text", "F9")
        settings = QSettings("MacroFlow", "MacroFlow")
        current = quick_text_delay_input(settings)
        value, ok = QInputDialog.getInt(
            self,
            f"{quick_text_key} 텍스트 재생 대기",
            f"새로 녹화하는 {quick_text_key} 텍스트 동작의 실행 전 대기 (ms):\n"
            "-1 = 녹화 타이밍 사용\n"
            " 0 = 직전 이벤트 종료 뒤 즉시 실행\n"
            "양수 = 지정 시간 대기 (재생 속도 배율 적용)\n"
            "권장 기본값 = 100 ms",
            current,
            -1,
            60_000,
            10,
        )
        if not ok:
            return
        settings.setValue(QUICK_TEXT_DELAY_KEY, value)
        label = "녹화 타이밍" if value < 0 else f"{value} ms"
        self._sb_state.setText(f"{quick_text_key} 텍스트 기본 재생 대기: {label}")

    def _show_color_check_settings(self) -> None:
        """현재 매크로와 앱 공통 색 체크 timeout/폴링 기본값을 편집한다."""
        if self._macro is None:
            QMessageBox.information(
                self,
                "색 체크 설정",
                "먼저 매크로를 녹화하거나 파일을 열어주세요.\n"
                "저장한 값은 현재 매크로와 앱 공통 기본값에 함께 반영됩니다.",
            )
            return

        settings = self._macro.settings
        dialog = QDialog(self)
        dialog.setWindowTitle("색 체크 설정")
        dialog.setFixedWidth(520)

        layout = QVBoxLayout(dialog)
        scope_help = QLabel(
            "현재 매크로에 저장되며 앱 공통 기본값으로도 기억됩니다. "
            "다른 매크로를 불러올 때도 이 기본값이 적용됩니다."
        )
        scope_help.setWordWrap(True)
        layout.addWidget(scope_help)

        click_group = QGroupBox("클릭 내부 색 체크")
        click_form = QFormLayout(click_group)
        click_help = QLabel(
            "색이 다르면 확인 주기마다 다시 검사합니다. timeout=0은 색이 일치할 때까지 "
            "무제한 대기합니다. timeout 만료 후 대기=클릭 진행, 무시=클릭 생략, "
            "중지=재생 중단입니다."
        )
        click_help.setWordWrap(True)
        click_form.addRow(click_help)
        click_wait_timeout = QSpinBox()
        click_wait_timeout.setRange(0, 600000)
        click_wait_timeout.setValue(settings.color_check_click_wait_timeout_ms)
        click_wait_timeout.setSuffix(" ms")
        click_wait_timeout.setSpecialValueText("무제한(일치까지)")
        click_wait_timeout.setToolTip("대기(wait) 모드에서 색이 맞을 때까지 기다릴 최대 시간")
        click_form.addRow("대기 timeout:", click_wait_timeout)

        click_skip_timeout = QSpinBox()
        click_skip_timeout.setRange(0, 600000)
        click_skip_timeout.setValue(settings.color_check_click_skip_timeout_ms)
        click_skip_timeout.setSuffix(" ms")
        click_skip_timeout.setSpecialValueText("무제한(일치까지)")
        click_skip_timeout.setToolTip("무시(skip) 모드에서 클릭을 건너뛰기 전 기다릴 최대 시간")
        click_form.addRow("무시 timeout:", click_skip_timeout)

        click_stop_timeout = QSpinBox()
        click_stop_timeout.setRange(0, 600000)
        click_stop_timeout.setValue(settings.color_check_click_stop_timeout_ms)
        click_stop_timeout.setSuffix(" ms")
        click_stop_timeout.setSpecialValueText("무제한(일치까지)")
        click_stop_timeout.setToolTip("중지(stop) 모드에서 재생을 중단하기 전 기다릴 최대 시간")
        click_form.addRow("중지 timeout:", click_stop_timeout)

        click_interval = QSpinBox()
        click_interval.setRange(1, 10000)
        click_interval.setValue(settings.color_check_click_interval_ms)
        click_interval.setSuffix(" ms")
        click_interval.setToolTip("클릭 색 체크 픽셀 폴링 주기")
        click_form.addRow("확인 주기:", click_interval)
        layout.addWidget(click_group)

        trigger_group = QGroupBox("독립 색 트리거")
        trigger_form = QFormLayout(trigger_group)
        trigger_help = QLabel(
            "새로 삽입하는 독립 색 트리거의 기본값입니다. 이미 삽입된 트리거의 "
            "개별 timeout/확인 주기는 바뀌지 않습니다."
        )
        trigger_help.setWordWrap(True)
        trigger_form.addRow(trigger_help)
        trigger_timeout = QSpinBox()
        trigger_timeout.setRange(0, 600000)
        trigger_timeout.setValue(settings.color_trigger_default_timeout_ms)
        trigger_timeout.setSuffix(" ms")
        trigger_timeout.setSpecialValueText("무제한(일치까지)")
        trigger_timeout.setToolTip("새로 삽입하는 ColorTriggerEvent의 기본 timeout")
        trigger_form.addRow("기본 timeout:", trigger_timeout)

        trigger_interval = QSpinBox()
        trigger_interval.setRange(1, 10000)
        trigger_interval.setValue(settings.color_trigger_check_interval_ms)
        trigger_interval.setSuffix(" ms")
        trigger_interval.setToolTip("새로 삽입하는 ColorTriggerEvent의 폴링 주기")
        trigger_form.addRow("확인 주기:", trigger_interval)
        layout.addWidget(trigger_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_settings = dataclasses.replace(
            settings,
            color_check_click_timeout_ms=click_skip_timeout.value(),
            color_check_click_wait_timeout_ms=click_wait_timeout.value(),
            color_check_click_skip_timeout_ms=click_skip_timeout.value(),
            color_check_click_stop_timeout_ms=click_stop_timeout.value(),
            color_check_click_interval_ms=click_interval.value(),
            color_trigger_default_timeout_ms=trigger_timeout.value(),
            color_trigger_check_interval_ms=trigger_interval.value(),
        )
        if new_settings == settings:
            return

        self._macro = dataclasses.replace(
            self._macro,
            settings=new_settings,
            is_edited=True,
        )
        self._editor.load_macro(self._macro)
        from PyQt6.QtCore import QSettings
        self._persist_color_settings(QSettings("MacroFlow", "MacroFlow"))
        self._update_range_spinboxes()
        self._update_toolbar()
        self._sb_state.setText("색 체크 설정 변경됨")

    def _on_sequence_done(self, _msg: str = "") -> None:
        """시퀀스 완료/오류 시 emergency hook 해제 후 툴바·상태바를 갱신한다."""
        if sys.platform == "win32":
            from macroflow.win32 import stop_emergency_hook
            stop_emergency_hook()
        self._overlay.stop()
        self._update_toolbar()
        self._sb_state.setText("대기 중")

    def _start_range_playback(self) -> None:
        """구간 재생 전용 버튼: 구간이 설정된 경우에만 1회 재생한다."""
        if self._state != "idle" or self._sequencer.is_running() or not self._macro:
            return
        if self._range_start_spin.value() == 0 and self._range_end_spin.value() == 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "구간 미설정",
                "구간 시작 또는 끝 값을 1 이상으로 설정한 후 재생하세요.\n"
                "(0=전체 재생은 ▶ 재생 버튼을 사용하세요)",
            )
            return
        event_range = self._calc_event_range()
        if event_range is None:
            return
        self._start_playback(options=range_playback_options(event_range))

    def _on_speed_combo_changed(self, idx: int) -> None:
        """속도 콤보 변경 처리. '직접 입력...' 선택 시 수동 입력 다이얼로그를 띄운다."""
        if idx != 6:
            return
        val, ok = QInputDialog.getDouble(
            self, "재생 속도 직접 입력",
            "배율을 입력하세요 (0.1 ~ 10.0):",
            value=self._custom_speed,
            min=0.1, max=10.0, decimals=1,
        )
        if ok:
            self._custom_speed = val
            self._speed_combo.setItemText(6, f"직접 ({val:.1f}x)")
        else:
            # 취소 시 이전 프리셋 인덱스로 되돌리기
            _presets = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
            best = min(range(6), key=lambda i: abs(_presets[i] - self._custom_speed))
            self._speed_combo.blockSignals(True)
            self._speed_combo.setCurrentIndex(best)
            self._speed_combo.blockSignals(False)

    def _on_play_event_range(self, start_idx: int, end_idx: int) -> None:
        """에디터에서 단일 이벤트 실행 요청 수신 시 해당 범위만 재생한다."""
        if self._state != "idle" or self._sequencer.is_running() or not self._macro:
            return
        self._start_playback(forced_range=(start_idx, end_idx))

    def _emergency_stop(self) -> None:
        logger.info("긴급 중지")
        # 시퀀서 실행 중이면 우선 중지
        if self._sequencer.is_running():
            stopped = self._sequencer.stop_sequence()
            self._overlay.stop()
            if sys.platform == "win32":
                from macroflow.win32 import stop_emergency_hook
                stop_emergency_hook()
            self._update_toolbar()
            if not stopped:
                self._sb_state.setText("긴급 중지 요청됨 — 시퀀스 worker 종료 대기 중")
        if self._state in {"recording", "stopping"}:
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
            is_player_playing = player.is_playing()
            if self._repeat_session is not None:
                self._overlay.set_repeat(
                    self._repeat_session.cycle_index + 1,
                    self._repeat_session.total,
                )
                if self._repeat_session.should_poll_wait_for_worker(
                    player_is_playing=is_player_playing
                ):
                    return
            if not is_player_playing:
                self._on_play_complete()

    # ── UI 갱신 ───────────────────────────────────────────────────────────────

    def _update_toolbar(self) -> None:
        is_idle = self._state == "idle"
        is_rec = self._state == "recording"
        is_stop = self._state == "stopping"
        is_play = self._state == "playing"
        is_seq_tab = self._is_sequencer_tab()
        is_fav_tab = self._is_favorites_tab()
        is_editor_tab = not is_seq_tab and not is_fav_tab
        seq_running = self._sequencer.is_running()
        runtime_recording_available = not (
            sys.platform == "win32"
            and self._hotkey_runtime is not None
            and not self._hotkey_runtime.globally_registered
        )
        record_key = self._hotkey_label("runtime.record_or_capture")
        play_key = self._hotkey_label("runtime.play_or_color_capture")
        pause_key = self._hotkey_label("runtime.pause_or_resume")

        # 녹화: 시퀀서·즐겨찾기 탭에서는 항상 비활성화
        self._act_record.setEnabled(
            (is_idle or is_rec or is_stop)
            and not seq_running
            and not is_seq_tab
            and not is_fav_tab
            and runtime_recording_available
        )
        self._act_record.setChecked(is_rec)
        if is_stop:
            self._act_record.setText(f"■ 중지 재시도 ({record_key})")
        elif is_rec and self._append_recording_mode:
            self._act_record.setText(f"■ 이어서 녹화 중지 ({record_key})")
        elif is_rec:
            self._act_record.setText(f"■ 중지 ({record_key})")
        else:
            self._act_record.setText(f"● 녹화 ({record_key})")
        can_append_record = (
            is_idle
            and not seq_running
            and self._macro is not None
            and not is_seq_tab
            and not is_fav_tab
            and runtime_recording_available
        )
        self._act_append_record.setEnabled(can_append_record)
        self._act_append_record_menu.setEnabled(can_append_record)
        self._act_new_record_menu.setEnabled(
            is_idle and not seq_running and is_editor_tab and runtime_recording_available
        )

        # 재생: 탭에 따라 텍스트와 활성화 조건이 달라짐
        if is_seq_tab:
            self._act_play.setEnabled(
                seq_running or (is_idle and bool(self._sequencer.has_items()))
            )
            self._act_play.setText(
                f"⏹ 중지 ({play_key})"
                if seq_running
                else f"▶ 시퀀스 실행 ({play_key})"
            )
        elif is_fav_tab:
            self._act_play.setEnabled(False)
            self._act_play.setText(f"▶ 재생 ({play_key})")
        else:
            self._act_play.setEnabled(
                is_play or (is_idle and not seq_running and self._macro is not None)
            )
            self._act_play.setText(
                f"⏹ 중지 ({play_key})" if is_play else f"▶ 재생 ({play_key})"
            )

        self._act_stop.setEnabled(is_rec or is_play or is_stop or seq_running)
        self._act_pause.setEnabled((is_rec or is_play) and not seq_running)
        self._act_pause.setText(
            f"▶ 계속 ({pause_key})"
            if self._paused
            else f"⏸ 일시중지 ({pause_key})"
        )
        self._act_range_play.setEnabled(
            is_idle and not seq_running and self._macro is not None and is_editor_tab
        )
        can_set_range = is_idle and not seq_running and is_editor_tab
        self._range_start_spin.setEnabled(can_set_range)
        self._range_end_spin.setEnabled(can_set_range)
        can_mutate_files = is_idle and not seq_running
        can_edit_macro_file = can_mutate_files and is_editor_tab
        self._act_open.setEnabled(can_edit_macro_file)
        self._act_save.setEnabled(can_edit_macro_file and self._macro is not None)
        self._act_save_as.setEnabled(can_edit_macro_file and self._macro is not None)
        self._act_save_seq.setEnabled(can_edit_macro_file and self._macro is not None)
        self._act_save_fav.setEnabled(can_edit_macro_file and self._macro is not None)
        self._act_restore_prev.setEnabled(
            can_edit_macro_file and self._prev_macro is not None
        )

        if is_seq_tab:
            self._menu_open.setText("플로우 열기...")
            self._menu_save.setText("플로우 저장")
            self._menu_save_as.setText("플로우 다른 이름으로 저장...")
            self._menu_open.setEnabled(can_mutate_files)
            self._menu_save.setEnabled(can_mutate_files and self._sequencer.has_items())
            self._menu_save_as.setEnabled(can_mutate_files and self._sequencer.has_items())
        elif is_fav_tab:
            self._menu_open.setText("열기...")
            self._menu_save.setText("저장")
            self._menu_save_as.setText("다른 이름으로 저장...")
            self._menu_open.setEnabled(False)
            self._menu_save.setEnabled(False)
            self._menu_save_as.setEnabled(False)
        else:
            self._menu_open.setText("매크로 열기...")
            self._menu_save.setText("매크로 저장")
            self._menu_save_as.setText("매크로 다른 이름으로 저장...")
            self._menu_open.setEnabled(can_mutate_files)
            self._menu_save.setEnabled(can_mutate_files and self._macro is not None)
            self._menu_save_as.setEnabled(can_mutate_files and self._macro is not None)

        # 시퀀서는 속도만 소비한다. 반복·간격은 단일 매크로 재생에만 적용한다.
        can_change_speed = is_idle and not seq_running and not is_fav_tab
        can_change_repeat = can_change_speed and is_editor_tab
        self._speed_combo.setEnabled(can_change_speed)
        self._repeat_spin.setEnabled(can_change_repeat)
        self._interval_spin.setEnabled(can_change_repeat)
        hotkeys_degraded = bool(
            self._hotkey_runtime is not None and self._hotkey_runtime.degraded
        )
        if hotkeys_degraded:
            self._act_record.setEnabled(False)
            self._act_append_record.setEnabled(False)
            self._act_append_record_menu.setEnabled(False)
            self._act_play.setEnabled(False)
            self._act_pause.setEnabled(False)
            self._act_range_play.setEnabled(False)
        self._act_hotkey_settings.setEnabled(
            is_idle and not seq_running and not hotkeys_degraded
        )

    def _update_range_spinboxes(self) -> None:
        """매크로 로드 후 구간 SpinBox 범위를 갱신한다."""
        total = self._editor.row_count()
        self._range_start_spin.setMaximum(max(total, 0))
        self._range_end_spin.setMaximum(max(total, 0))
        self._range_start_spin.setValue(0)
        self._range_end_spin.setValue(0)

    # ── 파일 조작 ─────────────────────────────────────────────────────────────

    def _sequence_file_mutation_blocked(self) -> bool:
        if not self._sequencer.is_running():
            return False
        self._sb_state.setText("시퀀스 실행 중에는 파일을 열거나 저장할 수 없습니다")
        return True

    def _get_default_dir(self) -> str:
        """파일 다이얼로그 초기 폴더를 반환한다.

        PyInstaller 패키징 상태이면 exe 파일이 있는 폴더,
        개발 환경이면 현재 작업 디렉토리를 반환한다.
        """
        if getattr(sys, "frozen", False):
            # PyInstaller 패키징 상태: sys.executable = ...MacroFlow.exe
            return str(Path(sys.executable).parent)
        return str(Path.cwd())

    def _open_file(self) -> None:
        if self._sequence_file_mutation_blocked():
            return
        if self._is_sequencer_tab():
            self._sequencer.open_flow()
            return
        if self._is_favorites_tab():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "매크로 파일 열기",
            self._get_default_dir(),
            "Macro JSON (*.json);;모든 파일 (*)",
        )
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str) -> None:
        """경로에서 매크로를 로드하여 에디터에 표시한다."""
        if self._sequence_file_mutation_blocked():
            return
        try:
            from macroflow import macro_file
            loaded_macro = macro_file.load(path)
            self._macro = self._apply_persisted_color_settings(loaded_macro)
            self._current_file = Path(path)
            self._editor.load_macro(self._macro)
            self._update_toolbar()
            self._update_range_spinboxes()
            self._sb_state.setText("파일 로드됨")
            self._sb_count.setText(f"이벤트: {len(self._macro.events)}")
            self.setWindowTitle(f"MacroFlow — {Path(path).name}")
            logger.info(f"파일 로드: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "파일 열기 오류", str(exc))
            logger.exception("파일 열기 오류")

    def _load_file_and_switch_tab(self, path: str) -> None:
        """시퀀서 더블클릭 시: 매크로를 로드하고 에디터 탭으로 전환한다."""
        if self._sequence_file_mutation_blocked():
            return
        self._load_file(path)
        self._tabs.setCurrentWidget(self._editor)

    def _on_merge_to_editor(self, macro: object) -> None:
        """시퀀서 '에디터로 병합' 결과를 에디터 탭에 로드한다.

        병합된 MacroData를 편집 가능한 상태로 에디터에 표시한다.
        저장 경로는 설정하지 않으므로, 저장 시 항상 '다른 이름으로 저장' 다이얼로그가 뜬다.
        """
        if not isinstance(macro, MacroData):
            return
        self._macro = macro
        self._current_file = None  # 병합 결과는 미저장 상태
        self._editor.load_macro(macro)
        self._tabs.setCurrentWidget(self._editor)
        self._update_toolbar()
        self._update_range_spinboxes()
        count = len(macro.events)
        self._sb_state.setText("병합 완료")
        self._sb_count.setText(f"이벤트: {count}")
        self.setWindowTitle("MacroFlow — [병합 매크로]")
        logger.info(f"시퀀서 병합 로드: {count}개 이벤트")

    def _save_file(self) -> None:
        """현재 파일에 덮어쓰기 저장한다.

        _current_file이 설정된 경우: 확인 다이얼로그 후 덮어쓰기.
        _current_file이 없는 경우: _save_file_as()로 위임.
        """
        if self._sequence_file_mutation_blocked():
            return
        if self._is_sequencer_tab():
            self._sequencer.save_flow()
            return
        if self._is_favorites_tab():
            return
        if not self._macro:
            return
        if self._current_file is None:
            self._save_file_as()
            return
        reply = QMessageBox.question(
            self,
            "덮어쓰기 저장",
            f"현재 파일에 덮어씁니다:\n\n{self._current_file}\n\n계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self._sequence_file_mutation_blocked():
            return
        self._do_save(str(self._current_file))

    def _save_file_as(self) -> None:
        if self._sequence_file_mutation_blocked():
            return
        if self._is_sequencer_tab():
            self._sequencer.save_flow_as()
            return
        if self._is_favorites_tab():
            return
        if not self._macro:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "매크로 저장",
            self._get_default_dir(),
            "Macro JSON (*.json)",
        )
        if not path:
            return
        if self._sequence_file_mutation_blocked():
            return
        if not path.endswith(".json"):
            path += ".json"
        if self._do_save(path):
            self._current_file = Path(path)
            self.setWindowTitle(f"MacroFlow — {Path(path).name}")

    def _do_save(self, path: str) -> bool:
        if self._sequence_file_mutation_blocked():
            return False
        if not self._macro:
            return False
        from macroflow import macro_file
        macro_file.save(self._macro, path)
        self._sb_state.setText(f"저장 완료: {Path(path).name}")
        logger.info(f"저장: {path}")
        return True

    def _get_macros_dir(self) -> Path:
        """영구 저장용 macros 디렉토리 경로를 반환한다.

        PyInstaller 패키징 상태이면 exe 파일 옆 macros/ 폴더,
        개발 환경이면 현재 작업 디렉토리 아래 macros/ 폴더를 사용한다.
        """
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent / "macros"
        return Path.cwd() / "macros"

    def _get_favorites_dir(self) -> Path:
        """즐겨찾기 저장용 favorites 디렉토리 경로를 반환한다.

        macros/ 와 별도의 favorites/ 폴더를 사용한다.
        """
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent / "favorites"
        return Path.cwd() / "favorites"

    def _save_and_add_to_favorites(self) -> None:
        """현재 매크로를 이름 입력 후 즐겨찾기 폴더에 저장하고 즐겨찾기 탭에 추가한다."""
        if self._sequence_file_mutation_blocked():
            return
        if not self._macro:
            return

        # 파일명 입력 받기
        suggested = self._current_file.stem if self._current_file else "즐겨찾기"
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setWindowTitle("즐겨찾기 이름 입력")
        dialog.setLabelText("저장할 이름을 입력하세요 (파일명으로 사용됩니다):")
        dialog.setTextValue(suggested)
        dialog.setMinimumWidth(640)
        dialog.resize(640, 160)
        ok = dialog.exec() == QDialog.DialogCode.Accepted
        name = dialog.textValue()
        if self._sequence_file_mutation_blocked():
            return
        if not ok or not name.strip():
            return

        name = name.strip()
        try:
            success = self._favorites.add_favorite(self._macro, name)
        except Exception as e:
            logger.exception(f"즐겨찾기 저장 중 예외: {e}")
            QMessageBox.critical(self, "즐겨찾기 저장 오류", f"예상치 못한 오류가 발생했습니다:\n{e}")
            return
        if success:
            self._tabs.setCurrentWidget(self._favorites)
            self._sb_state.setText(f"즐겨찾기 추가: {name}")
            logger.info(f"즐겨찾기 추가: {name}")
        else:
            QMessageBox.critical(self, "즐겨찾기 저장 오류", f"'{name}' 저장에 실패했습니다.")

    def _add_favorite_to_sequencer(self, path: str) -> None:
        """즐겨찾기 항목을 시퀀서에 추가한다."""
        if self._sequencer.is_running():
            return
        from pathlib import Path as _Path
        self._sequencer.add_macro_file(_Path(path))
        self._sb_state.setText(f"시퀀서 추가: {_Path(path).name}")

    def _restore_prev_macro(self) -> None:
        """이전 녹화를 복원한다.

        새 녹화를 시작하기 직전에 백업해 둔 매크로를 에디터에 로드한다.
        실수로 F6을 눌러 기존 매크로를 덮어쓴 경우에 사용한다.
        """
        if self._sequence_file_mutation_blocked():
            return
        if self._prev_macro is None:
            return

        reply = QMessageBox.question(
            self,
            "이전 매크로 복원",
            f"녹화 시작 전에 편집하던 매크로를 복원합니다.\n"
            f"이벤트 수: {len(self._prev_macro.events)}개\n\n"
            "현재 에디터의 내용은 임시 저장 파일로만 남습니다.\n계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self._sequence_file_mutation_blocked():
            return

        restored = self._prev_macro
        self._prev_macro = None
        self._macro = restored
        self._current_file = None
        self._editor.load_macro(restored)
        self._tabs.setCurrentWidget(self._editor)
        self._update_toolbar()
        self._update_range_spinboxes()
        count = len(restored.events)
        self._sb_state.setText("이전 매크로 복원됨")
        self._sb_count.setText(f"이벤트: {count}")
        self.setWindowTitle("MacroFlow — [복원된 매크로]")
        logger.info(f"이전 매크로 복원: {count}개 이벤트")

    def _auto_save_prev_recording(self, macro: MacroData) -> None:
        """새 녹화 시작 전 기존 매크로를 pre_recording_*.json 으로 임시 저장한다."""
        from datetime import datetime

        from macroflow import macro_file
        temp_dir = self._get_temp_dir()
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = temp_dir / f"pre_recording_{ts}.json"
            macro_file.save(macro, str(temp_file))
            logger.info(f"녹화 전 백업 저장: {temp_file.name}")
        except OSError as e:
            logger.warning(f"녹화 전 백업 저장 실패: {e}")

    def _save_and_add_to_sequencer(self) -> None:
        """macros 폴더에 날짜·시간 파일명으로 자동 저장 후 시퀀서에 추가한다.

        다이얼로그 없이 즉시 저장되며, 시퀀서 탭으로 자동 전환된다.
        """
        if self._sequence_file_mutation_blocked():
            return
        if not self._macro:
            return
        from datetime import datetime

        from macroflow import macro_file

        macros_dir = self._get_macros_dir()
        try:
            macros_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "폴더 생성 오류", str(e))
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = macros_dir / f"macro_{ts}.json"

        try:
            macro_file.save(self._macro, str(save_path))
        except OSError as e:
            QMessageBox.critical(self, "저장 오류", str(e))
            return

        self._current_file = save_path
        self.setWindowTitle(f"MacroFlow — {save_path.name}")
        self._sequencer.add_macro_file(save_path)
        self._tabs.setCurrentWidget(self._sequencer)
        self._sb_state.setText(f"시퀀서 추가: {save_path.name}")
        logger.info(f"시퀀서 자동 저장: {save_path}")

    # ── 매크로 변경 콜백 ─────────────────────────────────────────────────────

    def _on_macro_changed(self, macro: object) -> None:
        if isinstance(macro, MacroData):
            self._macro = macro
            self._update_range_spinboxes()

    # ── 최근 녹화 메뉴 ───────────────────────────────────────────────────────

    def _get_temp_dir(self) -> Path:
        """자동저장 디렉토리 경로를 반환한다."""
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path.home() / ".local" / "share"
        return base / "MacroFlow" / "temp"

    def _refresh_recent_menu(self) -> None:
        """최근 녹화 서브메뉴를 임시 저장 파일 목록으로 갱신한다."""
        self._recent_menu.clear()
        temp_dir = self._get_temp_dir()
        if not temp_dir.exists():
            act = self._recent_menu.addAction("(최근 녹화 없음)")
            act.setEnabled(False)
            return

        files = sorted(temp_dir.glob("recording_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            act = self._recent_menu.addAction("(최근 녹화 없음)")
            act.setEnabled(False)
            return

        for f in files[:_MAX_RECENT_SAVES]:
            act = self._recent_menu.addAction(f.name)
            file_path = str(f)
            act.triggered.connect(lambda checked=False, p=file_path: self._load_file(p))

    # ── 자동 저장 ─────────────────────────────────────────────────────────────

    def _auto_save_temp(self, macro: MacroData) -> None:
        from datetime import datetime

        from macroflow import macro_file
        temp_dir = self._get_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = temp_dir / f"recording_{ts}.json"
        macro_file.save(macro, str(temp_file))
        logger.info(f"임시 저장: {temp_file}")

        # 최근 10개만 유지, 나머지 삭제
        files = sorted(temp_dir.glob("recording_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old_file in files[_MAX_RECENT_SAVES:]:
            try:
                old_file.unlink()
                logger.debug(f"오래된 임시 파일 삭제: {old_file.name}")
            except OSError:
                pass

    def _show_about(self) -> None:
        from macroflow import __version__
        record = self._hotkey_label("runtime.record_or_capture")
        play = self._hotkey_label("runtime.play_or_color_capture")
        pause = self._hotkey_label("runtime.pause_or_resume")
        quick_text = self._hotkey_label("recording.quick_text")
        QMessageBox.about(
            self, "MacroFlow 정보",
            f"<b>MacroFlow v{__version__}</b><br><br>"
            "Windows 전용 마우스·키보드 매크로 녹화·재생 도구<br><br>"
            f"{record}: 녹화 시작/중지 또는 위치 캡처<br>"
            f"{play}: 재생 시작/중지 (녹화 중: 색상 체크 삽입)<br>"
            f"{pause}: 일시중지/계속<br>"
            f"{quick_text}: 빠른 텍스트 기록<br>"
            "ESC×3: 긴급 중지<br><br>"
            "구간 재생: 시작/끝 행 번호 설정 (0=전체)",
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
