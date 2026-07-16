# Graph Report - /root/.openclaw/workspace/macroflow  (2026-07-16)

## Corpus Check
- 104 files · ~85,440 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1393 nodes · 5159 edges · 38 communities detected
- Extraction: 39% EXTRACTED · 61% INFERRED · 0% AMBIGUOUS · INFERRED: 3135 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession|MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession]]
- [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings|MacroData MouseButtonEvent KeyEvent MacroSettings]]
- [[_COMMUNITY_execute event PlayState test|execute event PlayState test]]
- [[_COMMUNITY_EventEditorWidget add single row|EventEditorWidget add single row]]
- [[_COMMUNITY_EndNode MacroFlow FlowEngine MacroNode|EndNode MacroFlow FlowEngine MacroNode]]
- [[_COMMUNITY_FavoritesWidget refresh tree save|FavoritesWidget refresh tree save]]
- [[_COMMUNITY_TestTargetApp test target app.py|TestTargetApp test target app.py]]
- [[_COMMUNITY_build rows editor rows.py|build rows editor rows.py]]
- [[_COMMUNITY_test editor table.py table|test editor table.py table]]
- [[_COMMUNITY_.mouseMoveEvent TestPlaybackTiming play run|.mouseMoveEvent TestPlaybackTiming play run]]
- [[_COMMUNITY_test macro file.py load|test macro file.py load]]
- [[_COMMUNITY_convert raw TestConvertRaw stop|convert raw TestConvertRaw stop]]
- [[_COMMUNITY_test expression sandbox module.py|test expression sandbox module.py]]
- [[_COMMUNITY_mock.py find window get|mock.py find window get]]
- [[_COMMUNITY_rdp runtime safety smoke.py|rdp runtime safety smoke.py]]
- [[_COMMUNITY_test editor insertions.py insert|test editor insertions.py insert]]
- [[_COMMUNITY_test color settings regressions.py|test color settings regressions.py]]
- [[_COMMUNITY_test editor capture.py start|test editor capture.py start]]
- [[_COMMUNITY_key name test editor|key name test editor]]
- [[_COMMUNITY_main main.py setup logging|main main.py setup logging]]
- [[_COMMUNITY_test favorites search.py get|test favorites search.py get]]
- [[_COMMUNITY_summary text test editor|summary text test editor]]
- [[_COMMUNITY_test sequencer dirty state.py|test sequencer dirty state.py]]
- [[_COMMUNITY_conftest.py mock hook mock|conftest.py mock hook mock]]
- [[_COMMUNITY_test health contract.py test|test health contract.py test]]
- [[_COMMUNITY_test runtime safety.py run|test runtime safety.py run]]
- [[_COMMUNITY_test docs command contract.py|test docs command contract.py]]
- [[_COMMUNITY_test sequencer add item|test sequencer add item]]
- [[_COMMUNITY_test main window append|test main window append]]
- [[_COMMUNITY_test version.py test package|test version.py test package]]
- [[_COMMUNITY_test package imports.py test|test package imports.py test]]
- [[_COMMUNITY_test rdp gui smoke|test rdp gui smoke]]
- [[_COMMUNITY_test rdp gui smoke|test rdp gui smoke]]
- [[_COMMUNITY_Return whether complete repeat|Return whether complete repeat]]
- [[_COMMUNITY_Return user facing repeat|Return user facing repeat]]
- [[_COMMUNITY_init .py|init .py]]
- [[_COMMUNITY_run rdp runtime safety|run rdp runtime safety]]
- [[_COMMUNITY_run rdp gui smoke.ps1|run rdp gui smoke.ps1]]

## God Nodes (most connected - your core abstractions)
1. `MacroData` - 257 edges
2. `MouseButtonEvent` - 241 edges
3. `KeyEvent` - 180 edges
4. `MacroSettings` - 179 edges
5. `MouseMoveEvent` - 173 edges
6. `ColorTriggerEvent` - 170 edges
7. `TextInputEvent` - 165 edges
8. `MouseWheelEvent` - 151 edges
9. `WaitEvent` - 142 edges
10. `MacroMeta` - 127 edges

## Surprising Connections (you probably didn't know these)
- `Undo/history helpers for the MacroFlow event editor.  This module is intentional` --uses--> `MacroData`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_history.py → /root/.openclaw/workspace/macroflow/src/macroflow/types.py
- `Return a deep copy suitable for undo/redo snapshots.` --uses--> `MacroData`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_history.py → /root/.openclaw/workspace/macroflow/src/macroflow/types.py
- `Return a MacroData copy with a replaced event list.      Metadata, settings, and` --uses--> `MacroData`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_history.py → /root/.openclaw/workspace/macroflow/src/macroflow/types.py
- `Helpers for appending a fresh recording to an existing macro.  This module is in` --uses--> `MacroData`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py → /root/.openclaw/workspace/macroflow/src/macroflow/types.py
- `Return copies of ``events`` shifted so the first event starts at a timestamp.` --uses--> `MacroData`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/ui/append_recording.py → /root/.openclaw/workspace/macroflow/src/macroflow/types.py

## Communities

### Community 0 - "MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession"
Cohesion: 0.02
Nodes (84): Exception, 재생 중 ESC×3 긴급 중지 감지용 키보드 Hook을 시작한다.      LLKHF_INJECTED 이벤트(SendInput 주입)는 무시하므, 긴급 중지 Hook을 해제하고 스레드를 종료한다., start_emergency_hook(), stop_emergency_hook(), MainWindow, MacroFlow 메인 창.  전체 상태 머신(idle / recording / stopping / playing)을 관리한다. F6/F7 글로, 녹화 중 F7: 현재 마우스 커서 위치의 픽셀 색을 ColorTriggerEvent로 삽입한다. (+76 more)

### Community 1 - "MacroData MouseButtonEvent KeyEvent MacroSettings"
Cohesion: 0.07
Nodes (220): Pure event insertion helpers for the MacroFlow event editor.  This module intent, Return events with click or double-click MouseButtonEvents inserted., Return events with one configured ColorTriggerEvent inserted., Return the source event index after which an editor insertion should occur., Insert events after an index and shift following timestamps to preserve timing., Return events with one TextInputEvent inserted and later timestamps shifted., MacroFlow 이벤트 에디터 위젯.  그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력. Undo/Redo,, 지정 행 클릭 이벤트의 색 체크(color_check_enabled)를 토글한다.          recorded_color가 없는 이벤트에서는 (+212 more)

### Community 2 - "execute event PlayState test"
Cohesion: 0.03
Nodes (97): get_dpi_scale(), get_logical_screen_size(), pixel_to_ratio(), ratio_to_pixel(), Win32 DPI 스케일링 처리.  논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다. 모듈 임포트 시 SetProcessDpiAware, 기본 모니터의 논리 해상도를 반환한다 (DPI 스케일링 보정 후).      Returns:         (width, height) 픽셀 단, 시스템 DPI 배율을 반환한다 (96dpi 기준 1.0).      Returns:         DPI 배율. 예: 125% DPI → 1.2, 픽셀 절대 좌표를 화면 크기 대비 비율로 변환한다.      core-beliefs.md 원칙 4 — 녹화 시 비율로 저장, 재생 시 현재 해상 (+89 more)

### Community 3 - "EventEditorWidget add single row"
Cohesion: 0.04
Nodes (55): create_capture_controls(), create_delay_spin(), create_percentage_spin(), Small widget factories shared by MacroFlow editor dialogs., Create a position percentage spin box with the editor's shared bounds., Create a millisecond delay spin box with the editor's shared suffix., Create the standard F6 capture label/button pair used in editor dialogs., EventEditorWidget (+47 more)

### Community 4 - "EndNode MacroFlow FlowEngine MacroNode"
Cohesion: 0.06
Nodes (87): _color_matches(), ColorCheckNode, CounterNode, _dict_to_node(), EndNode, FlowEngine, FlowError, _hex_to_rgb() (+79 more)

### Community 5 - "FavoritesWidget refresh tree save"
Cohesion: 0.05
Nodes (37): move_filenames_to_group(), Pure helpers for Favorites batch actions.  The Favorites UI itself is PyQt-based, Return path names in first-seen order, dropping duplicates and blanks., Move filenames to a target group in-place without duplicating items., Remove filenames from every group in-place., remove_filenames_from_groups(), unique_filenames(), FavoritesTreeWidget (+29 more)

### Community 6 - "TestTargetApp test target app.py"
Cohesion: 0.07
Nodes (29): _click_events(), main(), parse_args(), _ratio(), run_gui_smoke(), append_event(), build_assertions(), initial_status() (+21 more)

### Community 7 - "build rows editor rows.py"
Cohesion: 0.1
Nodes (45): _apply_row_metadata(), _build_color_trigger_row(), _build_condition_row(), _build_key_down_row(), _build_key_up_row(), _build_loop_row(), _build_mouse_down_row(), _build_mouse_move_row() (+37 more)

### Community 8 - "test editor table.py table"
Cohesion: 0.07
Nodes (25): _cell(), _is_hex_color(), Qt table rendering helpers for the MacroFlow event editor.  This module intentio, QSS 색상 박스에 안전하게 사용할 수 있는 #RRGGBB 값인지 검사한다., 표시 row가 내용 열에 색상 swatch 위젯을 사용해야 하면 True를 반환한다., 표시 row 하나를 QTableWidgetItem 목록으로 렌더링한다., _should_use_color_detail_widget(), _table_row_items() (+17 more)

### Community 9 - ".mouseMoveEvent TestPlaybackTiming play run"
Cohesion: 0.09
Nodes (30): append_recording(), Helpers for appending a fresh recording to an existing macro.  This module is in, Return copies of ``events`` shifted so the first event starts at a timestamp., Append a newly recorded macro to ``base_macro`` and return a new MacroData., shift_event_timestamps(), get_progress(), play(), _key() (+22 more)

### Community 10 - "test macro file.py load"
Cohesion: 0.12
Nodes (37): _bounded_int(), delete_mouse_moves(), _dict_to_settings(), edit_key_value(), edit_position(), _event_to_dict(), load(), merge_macros() (+29 more)

### Community 11 - "convert raw TestConvertRaw stop"
Cohesion: 0.09
Nodes (13): WM_QUIT을 펌프 스레드에 보내 Hook을 해제하고 스레드를 종료한다., stop_hook(), _check_esc_triple(), _consumer_loop(), _convert_raw(), get_event_count(), inject_color_trigger(), is_recording() (+5 more)

### Community 12 - "test expression sandbox module.py"
Cohesion: 0.09
Nodes (25): _is_numeric_expression(), Pure validation rules for MacroFlow condition expressions.  This module owns the, Return whether an AST node is statically a numeric expression., Validate a sandbox wait value and return milliseconds as a float., Validate that an expression contains only the permitted AST surface., validate_expression(), validate_wait_ms(), execute_condition() (+17 more)

### Community 13 - "mock.py find window get"
Cohesion: 0.07
Nodes (15): find_window(), get_cursor_pos(), get_logical_screen_size(), get_pixel_color(), Win32 Mock 구현 — Linux/개발 환경용.  openclaw 같은 Linux 서버에서 Claude Code가 작업할 때 자동으로 사용, GetSystemMetrics Mock — 기본 1920×1080., Hook 등록 Mock — 아무것도 하지 않음., 테스트에서 GetPixel 반환값을 제어하기 위한 헬퍼. (+7 more)

### Community 14 - "rdp runtime safety smoke.py"
Cohesion: 0.18
Nodes (19): build_stop_macro(), evaluate_hotkey_result(), evaluate_sequencer_result(), format_status_line(), main(), _meta(), parse_args(), _press_function_key() (+11 more)

### Community 15 - "test editor insertions.py insert"
Cohesion: 0.22
Nodes (16): _base_timestamp_ns(), _insert_and_shift_events(), _insert_click_events(), _insert_color_trigger_event(), _insert_text_input_event(), _selected_insert_after_event_idx(), _ids(), test_insert_click_event_preserves_explicit_zero_delay() (+8 more)

### Community 16 - "test color settings regressions.py"
Cohesion: 0.12
Nodes (18): _color_check_timeout_ms_for_action(), 색 체크 timeout 세분화/지속성 회귀 테스트., 색 설정은 매크로 파일 저장 없이도 앱 설정으로 저장/복원되어야 한다., 대기/무시/중지 동작은 각자 독립 timeout 기본값을 가져야 한다., 일반 녹화/재생 오버레이도 hint처럼 위치 재설정+show/raise/update 경로를 타야 한다., 클릭 색 체크 runtime은 이벤트의 mismatch action별 timeout을 선택해야 한다., legacy timeout은 per-action timeout이 모두 기본값일 때만 사용한다., legacy 단일 timeout만 설정한 기존 호출 경로도 기존 값으로 동작해야 한다. (+10 more)

### Community 17 - "test editor capture.py start"
Cohesion: 0.24
Nodes (10): _FakeWidget, _import_editor(), _install_fake_pyqt(), _make_widget(), Event editor F6 capture lifecycle behavior with Qt mocked out., _Signal, test_cancel_f6_capture_only_emits_when_active(), test_consume_f6_capture_runs_once_and_emits_end() (+2 more)

### Community 18 - "key name test editor"
Cohesion: 0.22
Nodes (8): key_name_to_vk(), Key-name to Windows VK-code mapping for the MacroFlow event editor.  This module, 키 이름 문자열을 VK 코드로 변환한다.      1) NAME_TO_VK 딕셔너리에서 찾는다.     2) Windows 환경에서 단일 문자이, Editor key-name to VK-code mapping tests., 키 매핑 helper는 Qt 런타임 없이 독립 import 가능해야 한다., test_editor_keys_import_does_not_eagerly_import_pyqt_widgets(), test_key_name_to_vk_maps_standard_names_and_aliases(), test_key_name_to_vk_returns_fallback_for_unknown_name()

### Community 19 - "main main.py setup logging"
Cohesion: 0.36
Nodes (7): _fatal_dialog(), _get_log_dir(), main(), MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag, 파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다., Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목., _setup_logging()

### Community 20 - "test favorites search.py get"
Cohesion: 0.32
Nodes (7): _get_favorites_source(), 즐겨찾기 검색 필터 존재 여부 테스트., favorites.py 소스 코드를 직접 읽어 반환한다., FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다., FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다., test_favorites_widget_has_apply_search_filter(), test_favorites_widget_has_search_box_in_setup_ui()

### Community 21 - "summary text test editor"
Cohesion: 0.29
Nodes (6): Pure summary text helpers for the MacroFlow event editor., Return the event editor footer summary text., _summary_text(), Event editor summary text helper regression tests., test_summary_text_appends_edited_tag_when_macro_is_edited(), test_summary_text_matches_current_refresh_format_without_edited_tag()

### Community 22 - "test sequencer dirty state.py"
Cohesion: 0.43
Nodes (7): 시퀀서 미저장 변경 보호 회귀 테스트.  기존 일부 테스트가 collection 시점에 PyQt 모듈을 대체하므로 실제 Qt 검증은 독립 sub, _run_offscreen(), test_dirty_transitions_for_mutations_and_noops(), test_lossy_flow_projection_is_rejected(), test_main_window_dirty_tab_and_close_cancel(), test_save_load_and_save_as_failure_are_transactional(), test_unsaved_prompt_and_failed_open_preserve_state()

### Community 23 - "conftest.py mock hook mock"
Cohesion: 0.33
Nodes (5): mock_hook(), mock_win32(), pytest 공통 픽스처.  win32 모듈을 mock으로 교체하여 Linux 개발 환경에서도 테스트 가능하게 한다., win32 Platform Layer 전체를 Mock으로 대체한다.      Core 레이어 테스트 시 반드시 사용한다., start_hook / stop_hook을 mock으로 대체하고 직접 주입 가능한 큐를 반환한다.      테스트에서 이 큐에 raw 이벤트를

### Community 24 - "test health contract.py test"
Cohesion: 0.4
Nodes (4): 일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다., mouse_move 영구 삭제는 확인창을 거쳐야 한다., test_delete_mouse_moves_requires_confirmation_dialog(), test_play_toolbar_uses_stop_copy_while_playing()

### Community 25 - "test runtime safety.py run"
Cohesion: 0.6
Nodes (4): Real-PyQt subprocess regressions for runtime-only UI paths., _run_offscreen(), test_main_window_shortcut_fallback_uses_real_pyqt_shortcut(), test_sequencer_worker_callbacks_update_visible_state_on_gui_thread()

### Community 26 - "test docs command contract.py"
Cohesion: 0.4
Nodes (4): RDP smoke 관련 Linux 계약 테스트 문서는 uv run pytest 형태로 통일한다., CLAUDE 명령 예시는 바깥 active venv와 무관하게 프로젝트 .venv를 사용해야 한다., test_claude_commands_use_project_venv_friendly_uv_run(), test_linux_side_smoke_docs_use_uv_run_pytest()

### Community 27 - "test sequencer add item"
Cohesion: 0.4
Nodes (4): 존재하지 않는 파일은 시퀀서 목록 append 전에 차단해야 한다., 같은 매크로 경로는 중복 append 전에 차단해야 한다., test_add_item_rejects_duplicate_paths_before_append(), test_add_item_rejects_missing_files_before_append()

### Community 28 - "test main window append"
Cohesion: 0.5
Nodes (4): _question_calls_in_start_append_recording(), MainWindow 이어서 녹화 확인창 계약 테스트., 이어서 녹화 확인창은 Space만 눌러도 진행되도록 Yes를 기본 버튼으로 둔다., test_append_recording_confirmation_defaults_to_yes_for_spacebar()

### Community 29 - "test version.py test package"
Cohesion: 0.4
Nodes (4): 메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다., QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다., test_package_version_matches_project_metadata(), test_qapplication_version_uses_package_version()

### Community 30 - "test package imports.py test"
Cohesion: 0.5
Nodes (3): UI package import boundaries., 순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다., test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()

### Community 31 - "test rdp gui smoke"
Cohesion: 0.83
Nodes (3): _script_text(), test_runner_preserves_clipboard_summary_contract(), test_runner_redirects_stdout_and_stderr_without_powershell_error_records()

### Community 32 - "test rdp gui smoke"
Cohesion: 1.0
Nodes (2): _load_harness(), test_build_smoke_macro_exercises_windows_input_and_color_wait_paths()

### Community 33 - "Return whether complete repeat"
Cohesion: 1.0
Nodes (1): Return whether a complete repeat-session stop was requested.

### Community 34 - "Return user facing repeat"
Cohesion: 1.0
Nodes (1): Return user-facing repeat cycle label, e.g. '3/10회'.

### Community 35 - "init .py"
Cohesion: 1.0
Nodes (0):

### Community 36 - "run rdp runtime safety"
Cohesion: 1.0
Nodes (0):

### Community 37 - "run rdp gui smoke.ps1"
Cohesion: 1.0
Nodes (0):

## Knowledge Gaps
- **167 isolated node(s):** `MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag`, `파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다.`, `Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목.`, `Pure validation rules for MacroFlow condition expressions.  This module owns the`, `Return whether an AST node is statically a numeric expression.` (+162 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Return whether complete repeat`** (1 nodes): `Return whether a complete repeat-session stop was requested.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Return user facing repeat`** (1 nodes): `Return user-facing repeat cycle label, e.g. '3/10회'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `init .py`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `run rdp runtime safety`** (1 nodes): `run_rdp_runtime_safety_smoke.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `run rdp gui smoke.ps1`** (1 nodes): `run_rdp_gui_smoke.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MacroData` connect `MacroData MouseButtonEvent KeyEvent MacroSettings` to `MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession`, `execute event PlayState test`, `EventEditorWidget add single row`, `EndNode MacroFlow FlowEngine MacroNode`, `.mouseMoveEvent TestPlaybackTiming play run`, `test macro file.py load`, `convert raw TestConvertRaw stop`, `rdp runtime safety smoke.py`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `EventEditorWidget` connect `EventEditorWidget add single row` to `MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession`, `test editor table.py table`, `test editor capture.py start`, `MacroData MouseButtonEvent KeyEvent MacroSettings`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession` to `MacroData MouseButtonEvent KeyEvent MacroSettings`, `execute event PlayState test`, `EventEditorWidget add single row`, `FavoritesWidget refresh tree save`, `rdp runtime safety smoke.py`, `main main.py setup logging`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 255 inferred relationships involving `MacroData` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MacroData` has 255 INFERRED edges - model-reasoned connections that need verification._
- **Are the 238 inferred relationships involving `MouseButtonEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MouseButtonEvent` has 238 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `KeyEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`KeyEvent` has 177 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `MacroSettings` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MacroSettings` has 177 INFERRED edges - model-reasoned connections that need verification._