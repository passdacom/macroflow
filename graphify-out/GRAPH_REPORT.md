# Graph Report - .  (2026-07-16)

## Corpus Check
- 104 files · ~85,789 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1395 nodes · 5170 edges · 37 communities detected
- Extraction: 39% EXTRACTED · 61% INFERRED · 0% AMBIGUOUS · INFERRED: 3143 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings|MacroData MouseButtonEvent KeyEvent MacroSettings]]
- [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions|MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine|MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- [[_COMMUNITY_execute event PlayState test|execute event PlayState test]]
- [[_COMMUNITY_EventEditorWidget add single row|EventEditorWidget add single row]]
- [[_COMMUNITY_FavoritesWidget refresh tree save|FavoritesWidget refresh tree save]]
- [[_COMMUNITY_mock.py hooks.py get logical|mock.py hooks.py get logical]]
- [[_COMMUNITY_TestTargetApp test target app.py|TestTargetApp test target app.py]]
- [[_COMMUNITY_build rows editor rows.py|build rows editor rows.py]]
- [[_COMMUNITY_test editor table.py table|test editor table.py table]]
- [[_COMMUNITY_test macro file.py load|test macro file.py load]]
- [[_COMMUNITY_convert raw TestConvertRaw recorder.py|convert raw TestConvertRaw recorder.py]]
- [[_COMMUNITY_test expression sandbox module.py|test expression sandbox module.py]]
- [[_COMMUNITY_rdp runtime safety smoke.py|rdp runtime safety smoke.py]]
- [[_COMMUNITY_test editor insertions.py insert|test editor insertions.py insert]]
- [[_COMMUNITY_append recording test append|append recording test append]]
- [[_COMMUNITY_test editor context menu.py|test editor context menu.py]]
- [[_COMMUNITY_key name test editor|key name test editor]]
- [[_COMMUNITY_main main.py setup logging|main main.py setup logging]]
- [[_COMMUNITY_summary text test editor|summary text test editor]]
- [[_COMMUNITY_test favorites search.py get|test favorites search.py get]]
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
1. `MacroData` - 258 edges
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
  ./src/macroflow/ui/editor_history.py → ./src/macroflow/types.py
- `Return a deep copy suitable for undo/redo snapshots.` --uses--> `MacroData`  [INFERRED]
  ./src/macroflow/ui/editor_history.py → ./src/macroflow/types.py
- `Return a MacroData copy with a replaced event list.      Metadata, settings, and` --uses--> `MacroData`  [INFERRED]
  ./src/macroflow/ui/editor_history.py → ./src/macroflow/types.py
- `Helpers for appending a fresh recording to an existing macro.  This module is in` --uses--> `MacroData`  [INFERRED]
  ./src/macroflow/ui/append_recording.py → ./src/macroflow/types.py
- `Return copies of ``events`` shifted so the first event starts at a timestamp.` --uses--> `MacroData`  [INFERRED]
  ./src/macroflow/ui/append_recording.py → ./src/macroflow/types.py

## Communities

### Community 0 - "MacroData MouseButtonEvent KeyEvent MacroSettings"
Cohesion: 0.07
Nodes (222): Pure event insertion helpers for the MacroFlow event editor.  This module intent, Return events with click or double-click MouseButtonEvents inserted., Return events with one configured ColorTriggerEvent inserted., Return the source event index after which an editor insertion should occur., Insert events after an index and shift following timestamps to preserve timing., Return events with one TextInputEvent inserted and later timestamps shifted., MacroFlow 이벤트 에디터 위젯.  그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력. Undo/Redo,, 지정 행 클릭 이벤트의 색 체크(color_check_enabled)를 토글한다.          recorded_color가 없는 이벤트에서는 (+214 more)

### Community 1 - "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
Cohesion: 0.03
Nodes (88): pixel_to_ratio(), 픽셀 절대 좌표를 화면 크기 대비 비율로 변환한다.      core-beliefs.md 원칙 4 — 녹화 시 비율로 저장, 재생 시 현재 해상, Exception, 재생 중 ESC×3 긴급 중지 감지용 키보드 Hook을 시작한다.      LLKHF_INJECTED 이벤트(SendInput 주입)는 무시하므, 긴급 중지 Hook을 해제하고 스레드를 종료한다., start_emergency_hook(), stop_emergency_hook(), MainWindow (+80 more)

### Community 2 - "MacroSequencerWidget EndNode MacroFlow FlowEngine"
Cohesion: 0.04
Nodes (96): _key(), _macro(), main(), _meta(), _move(), parse_args(), _rewrite_flow_with_dot_segments(), run_smoke() (+88 more)

### Community 3 - "execute event PlayState test"
Cohesion: 0.03
Nodes (92): find_window(), get_pixel_color(), GetPixel로 단일 픽셀 RGB 값을 반환한다.      core-beliefs.md 원칙 7: 스크린샷 API 금지 — GetPixel만, title_contains를 제목에 포함하는 창 핸들(HWND)을 반환한다.      Args:         title_contains: 검색, _color_check_timeout_ms_for_action(), _color_matches(), _event_timing_compensation_ns(), _execute_event() (+84 more)

### Community 4 - "EventEditorWidget add single row"
Cohesion: 0.04
Nodes (55): create_capture_controls(), create_delay_spin(), create_percentage_spin(), Small widget factories shared by MacroFlow editor dialogs., Create a position percentage spin box with the editor's shared bounds., Create a millisecond delay spin box with the editor's shared suffix., Create the standard F6 capture label/button pair used in editor dialogs., EventEditorWidget (+47 more)

### Community 5 - "FavoritesWidget refresh tree save"
Cohesion: 0.05
Nodes (38): move_filenames_to_group(), Pure helpers for Favorites batch actions.  The Favorites UI itself is PyQt-based, Return path names in first-seen order, dropping duplicates and blanks., Move filenames to a target group in-place without duplicating items., Remove filenames from every group in-place., remove_filenames_from_groups(), unique_filenames(), FavoritesTreeWidget (+30 more)

### Community 6 - "mock.py hooks.py get logical"
Cohesion: 0.03
Nodes (46): get_dpi_scale(), get_logical_screen_size(), ratio_to_pixel(), Win32 DPI 스케일링 처리.  논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다. 모듈 임포트 시 SetProcessDpiAware, 기본 모니터의 논리 해상도를 반환한다 (DPI 스케일링 보정 후).      Returns:         (width, height) 픽셀 단, 시스템 DPI 배율을 반환한다 (96dpi 기준 1.0).      Returns:         DPI 배율. 예: 125% DPI → 1.2, 화면 비율 좌표를 현재 해상도의 픽셀 좌표로 변환한다.      Args:         x_ratio: X 좌표 비율 (0.0~1.0)., _emg_keyboard_proc() (+38 more)

### Community 7 - "TestTargetApp test target app.py"
Cohesion: 0.07
Nodes (29): _click_events(), main(), parse_args(), _ratio(), run_gui_smoke(), append_event(), build_assertions(), initial_status() (+21 more)

### Community 8 - "build rows editor rows.py"
Cohesion: 0.1
Nodes (45): _apply_row_metadata(), _build_color_trigger_row(), _build_condition_row(), _build_key_down_row(), _build_key_up_row(), _build_loop_row(), _build_mouse_down_row(), _build_mouse_move_row() (+37 more)

### Community 9 - "test editor table.py table"
Cohesion: 0.07
Nodes (25): _cell(), _is_hex_color(), Qt table rendering helpers for the MacroFlow event editor.  This module intentio, QSS 색상 박스에 안전하게 사용할 수 있는 #RRGGBB 값인지 검사한다., 표시 row가 내용 열에 색상 swatch 위젯을 사용해야 하면 True를 반환한다., 표시 row 하나를 QTableWidgetItem 목록으로 렌더링한다., _should_use_color_detail_widget(), _table_row_items() (+17 more)

### Community 10 - "test macro file.py load"
Cohesion: 0.12
Nodes (37): _bounded_int(), delete_mouse_moves(), _dict_to_settings(), edit_key_value(), edit_position(), _event_to_dict(), load(), merge_macros() (+29 more)

### Community 11 - "convert raw TestConvertRaw recorder.py"
Cohesion: 0.11
Nodes (9): _check_esc_triple(), _consumer_loop(), _convert_raw(), get_event_count(), inject_color_trigger(), is_recording(), _vk_to_key(), TestConvertRaw (+1 more)

### Community 12 - "test expression sandbox module.py"
Cohesion: 0.09
Nodes (25): _is_numeric_expression(), Pure validation rules for MacroFlow condition expressions.  This module owns the, Return whether an AST node is statically a numeric expression., Validate a sandbox wait value and return milliseconds as a float., Validate that an expression contains only the permitted AST surface., validate_expression(), validate_wait_ms(), execute_condition() (+17 more)

### Community 13 - "rdp runtime safety smoke.py"
Cohesion: 0.17
Nodes (20): is_playing(), build_stop_macro(), evaluate_hotkey_result(), evaluate_sequencer_result(), format_status_line(), main(), _meta(), parse_args() (+12 more)

### Community 14 - "test editor insertions.py insert"
Cohesion: 0.22
Nodes (16): _base_timestamp_ns(), _insert_and_shift_events(), _insert_click_events(), _insert_color_trigger_event(), _insert_text_input_event(), _selected_insert_after_event_idx(), _ids(), test_insert_click_event_preserves_explicit_zero_delay() (+8 more)

### Community 15 - "append recording test append"
Cohesion: 0.27
Nodes (11): append_recording(), Helpers for appending a fresh recording to an existing macro.  This module is in, Return copies of ``events`` shifted so the first event starts at a timestamp., Append a newly recorded macro to ``base_macro`` and return a new MacroData., shift_event_timestamps(), _key(), _macro(), _move() (+3 more)

### Community 16 - "test editor context menu.py"
Cohesion: 0.4
Nodes (9): _action_texts(), _FakeMenu, _import_editor(), _install_fake_pyqt(), _macro_with_event(), _macro_with_events(), _make_widget(), test_single_color_checked_click_menu_includes_color_policy_submenu() (+1 more)

### Community 17 - "key name test editor"
Cohesion: 0.22
Nodes (8): key_name_to_vk(), Key-name to Windows VK-code mapping for the MacroFlow event editor.  This module, 키 이름 문자열을 VK 코드로 변환한다.      1) NAME_TO_VK 딕셔너리에서 찾는다.     2) Windows 환경에서 단일 문자이, Editor key-name to VK-code mapping tests., 키 매핑 helper는 Qt 런타임 없이 독립 import 가능해야 한다., test_editor_keys_import_does_not_eagerly_import_pyqt_widgets(), test_key_name_to_vk_maps_standard_names_and_aliases(), test_key_name_to_vk_returns_fallback_for_unknown_name()

### Community 18 - "main main.py setup logging"
Cohesion: 0.36
Nodes (7): _fatal_dialog(), _get_log_dir(), main(), MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag, 파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다., Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목., _setup_logging()

### Community 19 - "summary text test editor"
Cohesion: 0.29
Nodes (6): Pure summary text helpers for the MacroFlow event editor., Return the event editor footer summary text., _summary_text(), Event editor summary text helper regression tests., test_summary_text_appends_edited_tag_when_macro_is_edited(), test_summary_text_matches_current_refresh_format_without_edited_tag()

### Community 20 - "test favorites search.py get"
Cohesion: 0.32
Nodes (7): _get_favorites_source(), 즐겨찾기 검색 필터 존재 여부 테스트., favorites.py 소스 코드를 직접 읽어 반환한다., FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다., FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다., test_favorites_widget_has_apply_search_filter(), test_favorites_widget_has_search_box_in_setup_ui()

### Community 21 - "test sequencer dirty state.py"
Cohesion: 0.43
Nodes (7): 시퀀서 미저장 변경 보호 회귀 테스트.  기존 일부 테스트가 collection 시점에 PyQt 모듈을 대체하므로 실제 Qt 검증은 독립 sub, _run_offscreen(), test_dirty_transitions_for_mutations_and_noops(), test_lossy_flow_projection_is_rejected(), test_main_window_dirty_tab_and_close_cancel(), test_save_load_and_save_as_failure_are_transactional(), test_unsaved_prompt_and_failed_open_preserve_state()

### Community 22 - "conftest.py mock hook mock"
Cohesion: 0.33
Nodes (5): mock_hook(), mock_win32(), pytest 공통 픽스처.  win32 모듈을 mock으로 교체하여 Linux 개발 환경에서도 테스트 가능하게 한다., win32 Platform Layer 전체를 Mock으로 대체한다.      Core 레이어 테스트 시 반드시 사용한다., start_hook / stop_hook을 mock으로 대체하고 직접 주입 가능한 큐를 반환한다.      테스트에서 이 큐에 raw 이벤트를

### Community 23 - "test health contract.py test"
Cohesion: 0.4
Nodes (4): 일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다., mouse_move 영구 삭제는 확인창을 거쳐야 한다., test_delete_mouse_moves_requires_confirmation_dialog(), test_play_toolbar_uses_stop_copy_while_playing()

### Community 24 - "test runtime safety.py run"
Cohesion: 0.6
Nodes (4): Real-PyQt subprocess regressions for runtime-only UI paths., _run_offscreen(), test_main_window_shortcut_fallback_uses_real_pyqt_shortcut(), test_sequencer_worker_callbacks_update_visible_state_on_gui_thread()

### Community 25 - "test docs command contract.py"
Cohesion: 0.4
Nodes (4): RDP smoke 관련 Linux 계약 테스트 문서는 uv run pytest 형태로 통일한다., CLAUDE 명령 예시는 바깥 active venv와 무관하게 프로젝트 .venv를 사용해야 한다., test_claude_commands_use_project_venv_friendly_uv_run(), test_linux_side_smoke_docs_use_uv_run_pytest()

### Community 26 - "test sequencer add item"
Cohesion: 0.4
Nodes (4): 존재하지 않는 파일은 시퀀서 목록 append 전에 차단해야 한다., 같은 매크로 경로는 중복 append 전에 차단해야 한다., test_add_item_rejects_duplicate_paths_before_append(), test_add_item_rejects_missing_files_before_append()

### Community 27 - "test main window append"
Cohesion: 0.5
Nodes (4): _question_calls_in_start_append_recording(), MainWindow 이어서 녹화 확인창 계약 테스트., 이어서 녹화 확인창은 Space만 눌러도 진행되도록 Yes를 기본 버튼으로 둔다., test_append_recording_confirmation_defaults_to_yes_for_spacebar()

### Community 28 - "test version.py test package"
Cohesion: 0.4
Nodes (4): 메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다., QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다., test_package_version_matches_project_metadata(), test_qapplication_version_uses_package_version()

### Community 29 - "test package imports.py test"
Cohesion: 0.5
Nodes (3): UI package import boundaries., 순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다., test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()

### Community 30 - "test rdp gui smoke"
Cohesion: 0.83
Nodes (3): _script_text(), test_runner_preserves_clipboard_summary_contract(), test_runner_redirects_stdout_and_stderr_without_powershell_error_records()

### Community 31 - "test rdp gui smoke"
Cohesion: 1.0
Nodes (2): _load_harness(), test_build_smoke_macro_exercises_windows_input_and_color_wait_paths()

### Community 32 - "Return whether complete repeat"
Cohesion: 1.0
Nodes (1): Return whether a complete repeat-session stop was requested.

### Community 33 - "Return user facing repeat"
Cohesion: 1.0
Nodes (1): Return user-facing repeat cycle label, e.g. '3/10회'.

### Community 34 - "init .py"
Cohesion: 1.0
Nodes (0):

### Community 35 - "run rdp runtime safety"
Cohesion: 1.0
Nodes (0):

### Community 36 - "run rdp gui smoke.ps1"
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

- **Why does `MacroData` connect `MacroData MouseButtonEvent KeyEvent MacroSettings` to `MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions`, `MacroSequencerWidget EndNode MacroFlow FlowEngine`, `execute event PlayState test`, `EventEditorWidget add single row`, `test macro file.py load`, `rdp runtime safety smoke.py`, `append recording test append`, `test editor context menu.py`?**
  _High betweenness centrality (0.240) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions` to `MacroData MouseButtonEvent KeyEvent MacroSettings`, `MacroSequencerWidget EndNode MacroFlow FlowEngine`, `EventEditorWidget add single row`, `FavoritesWidget refresh tree save`, `mock.py hooks.py get logical`, `rdp runtime safety smoke.py`, `main main.py setup logging`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `EventEditorWidget` connect `EventEditorWidget add single row` to `MacroData MouseButtonEvent KeyEvent MacroSettings`, `MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions`, `test editor table.py table`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 256 inferred relationships involving `MacroData` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MacroData` has 256 INFERRED edges - model-reasoned connections that need verification._
- **Are the 238 inferred relationships involving `MouseButtonEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MouseButtonEvent` has 238 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `KeyEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`KeyEvent` has 177 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `MacroSettings` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MacroSettings` has 177 INFERRED edges - model-reasoned connections that need verification._