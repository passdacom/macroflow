# Graph Report - /root/.openclaw/workspace/macroflow  (2026-07-23)

## Corpus Check
- 78 files · ~86,623 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1440 nodes · 5358 edges · 39 communities detected
- Extraction: 38% EXTRACTED · 62% INFERRED · 0% AMBIGUOUS · INFERRED: 3308 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]

## God Nodes (most connected - your core abstractions)
1. `MacroData` - 278 edges
2. `MouseButtonEvent` - 241 edges
3. `KeyEvent` - 180 edges
4. `MacroSettings` - 179 edges
5. `MouseMoveEvent` - 173 edges
6. `ColorTriggerEvent` - 170 edges
7. `TextInputEvent` - 165 edges
8. `MouseWheelEvent` - 151 edges
9. `WaitEvent` - 142 edges
10. `ConditionEvent` - 132 edges

## Surprising Connections (you probably didn't know these)
- `MacroNode` --uses--> `ConditionEvent`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py → ./src/macroflow/types.py
- `MacroNode` --uses--> `LoopEvent`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py → ./src/macroflow/types.py
- `ColorCheckNode` --uses--> `ConditionEvent`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py → ./src/macroflow/types.py
- `ColorCheckNode` --uses--> `LoopEvent`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py → ./src/macroflow/types.py
- `ColorCheckNode` --uses--> `End-to-end regressions discovered by the 2026-07 functional audit.`  [INFERRED]
  /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py → ./tests/test_functional_audit_regressions.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (244): Pure event insertion helpers for the MacroFlow event editor.  This module intent, Return events with click or double-click MouseButtonEvents inserted., Return events with one configured ColorTriggerEvent inserted., Return the source event index after which an editor insertion should occur., Insert events after an index and shift following timestamps to preserve timing., Return events with one TextInputEvent inserted and later timestamps shifted., MacroFlow 이벤트 에디터 위젯.  그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력. Undo/Redo,, 지정 행 클릭 이벤트의 색 체크(color_check_enabled)를 토글한다.          recorded_color가 없는 이벤트에서는 (+236 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (94): pixel_to_ratio(), 픽셀 절대 좌표를 화면 크기 대비 비율로 변환한다.      core-beliefs.md 원칙 4 — 녹화 시 비율로 저장, 재생 시 현재 해상, EventEditorWidget, Exception, FavoritesWidget, MacroFlow 즐겨찾기 위젯 (트리 구조).  즐겨찾기를 그룹별로 분류하고 아코디언 트리 뷰로 표시한다. 그룹과 항목 모두 드래그앤드롭으로, 즐겨찾기 트리 위젯.      favorites/ 디렉토리와 _index.json 파일을 함께 관리한다.     새로 추가된 항목은 기본 그룹(, 즐겨찾기 디렉토리를 설정하고 트리를 초기 로드한다. (+86 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (118): Hook을 등록하고 메시지 펌프 스레드를 시작한다.      Args:         queue: 캡처된 원시 이벤트를 쌓을 deque., start_hook(), start_recording(), _color_matches(), ColorCheckNode, CounterNode, _dict_to_node(), EndNode (+110 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (58): create_capture_controls(), create_delay_spin(), create_percentage_spin(), Small widget factories shared by MacroFlow editor dialogs., Create a position percentage spin box with the editor's shared bounds., Create a millisecond delay spin box with the editor's shared suffix., Create the standard F6 capture label/button pair used in editor dialogs., copy_events() (+50 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (55): get_pixel_color(), GetPixel로 단일 픽셀 RGB 값을 반환한다.      core-beliefs.md 원칙 7: 스크린샷 API 금지 — GetPixel만, _color_check_timeout_ms_for_action(), _color_matches(), _event_timing_compensation_ns(), _execute_event_sequence(), get_current_event_idx(), get_progress() (+47 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (29): move_filenames_to_group(), Pure helpers for Favorites batch actions.  The Favorites UI itself is PyQt-based, Return path names in first-seen order, dropping duplicates and blanks., Move filenames to a target group in-place without duplicating items., Remove filenames from every group in-place., remove_filenames_from_groups(), unique_filenames(), MacroData를 즐겨찾기 폴더에 저장하고 기본 그룹에 추가한다.          Args:             macro_data: 저장할 (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (45): get_dpi_scale(), get_logical_screen_size(), ratio_to_pixel(), Win32 DPI 스케일링 처리.  논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다. 모듈 임포트 시 SetProcessDpiAware, 기본 모니터의 논리 해상도를 반환한다 (DPI 스케일링 보정 후).      Returns:         (width, height) 픽셀 단, 시스템 DPI 배율을 반환한다 (96dpi 기준 1.0).      Returns:         DPI 배율. 예: 125% DPI → 1.2, 화면 비율 좌표를 현재 해상도의 픽셀 좌표로 변환한다.      Args:         x_ratio: X 좌표 비율 (0.0~1.0)., Win32 API 레이어.  Windows에서는 실제 ctypes 구현을 사용. Linux/개발 환경(openclaw 등)에서는 Mock을 자동 (+37 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (33): _emg_keyboard_proc(), _emg_pump(), find_window(), get_cursor_pos(), _KBDLLHOOKSTRUCT, _keyboard_proc(), _message_pump(), _mouse_proc() (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (29): _click_events(), main(), parse_args(), _ratio(), run_gui_smoke(), append_event(), build_assertions(), initial_status() (+21 more)

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (45): _apply_row_metadata(), _build_color_trigger_row(), _build_condition_row(), _build_key_down_row(), _build_key_up_row(), _build_loop_row(), _build_mouse_down_row(), _build_mouse_move_row() (+37 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (25): _cell(), _is_hex_color(), Qt table rendering helpers for the MacroFlow event editor.  This module intentio, QSS 색상 박스에 안전하게 사용할 수 있는 #RRGGBB 값인지 검사한다., 표시 row가 내용 열에 색상 swatch 위젯을 사용해야 하면 True를 반환한다., 표시 row 하나를 QTableWidgetItem 목록으로 렌더링한다., _should_use_color_detail_widget(), _table_row_items() (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (39): _bounded_int(), delete_mouse_moves(), _dict_to_settings(), edit_key_value(), edit_position(), _event_to_dict(), load(), merge_macros() (+31 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (25): _is_numeric_expression(), Pure validation rules for MacroFlow condition expressions.  This module owns the, Return whether an AST node is statically a numeric expression., Validate a sandbox wait value and return milliseconds as a float., Validate that an expression contains only the permitted AST surface., validate_expression(), validate_wait_ms(), execute_condition() (+17 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (19): build_stop_macro(), evaluate_hotkey_result(), evaluate_sequencer_result(), format_status_line(), main(), _meta(), parse_args(), _press_function_key() (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.26
Nodes (14): _base_timestamp_ns(), _insert_and_shift_events(), _insert_click_events(), _insert_color_trigger_event(), _insert_text_input_event(), _selected_insert_after_event_idx(), _ids(), test_insert_click_event_preserves_explicit_zero_delay() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.24
Nodes (10): _FakeWidget, _import_editor(), _install_fake_pyqt(), _make_widget(), Event editor F6 capture lifecycle behavior with Qt mocked out., _Signal, test_cancel_f6_capture_only_emits_when_active(), test_consume_f6_capture_runs_once_and_emits_end() (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.27
Nodes (11): append_recording(), Helpers for appending a fresh recording to an existing macro.  This module is in, Return copies of ``events`` shifted so the first event starts at a timestamp., Append a newly recorded macro to ``base_macro`` and return a new MacroData., shift_event_timestamps(), _key(), _macro(), _move() (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.22
Nodes (8): key_name_to_vk(), Key-name to Windows VK-code mapping for the MacroFlow event editor.  This module, 키 이름 문자열을 VK 코드로 변환한다.      1) NAME_TO_VK 딕셔너리에서 찾는다.     2) Windows 환경에서 단일 문자이, Editor key-name to VK-code mapping tests., 키 매핑 helper는 Qt 런타임 없이 독립 import 가능해야 한다., test_editor_keys_import_does_not_eagerly_import_pyqt_widgets(), test_key_name_to_vk_maps_standard_names_and_aliases(), test_key_name_to_vk_returns_fallback_for_unknown_name()

### Community 18 - "Community 18"
Cohesion: 0.39
Nodes (8): 시퀀서 미저장 변경 보호 회귀 테스트.  기존 일부 테스트가 collection 시점에 PyQt 모듈을 대체하므로 실제 Qt 검증은 독립 sub, _run_offscreen(), test_dirty_transitions_for_mutations_and_noops(), test_linear_flow_with_noncanonical_document_data_is_rejected(), test_lossy_flow_projection_is_rejected(), test_main_window_dirty_tab_and_close_cancel(), test_save_load_and_save_as_failure_are_transactional(), test_unsaved_prompt_and_failed_open_preserve_state()

### Community 19 - "Community 19"
Cohesion: 0.42
Nodes (8): _key(), _macro(), main(), _meta(), _move(), parse_args(), _rewrite_flow_with_dot_segments(), run_smoke()

### Community 20 - "Community 20"
Cohesion: 0.36
Nodes (7): _fatal_dialog(), _get_log_dir(), main(), MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag, 파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다., Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목., _setup_logging()

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (6): Pure summary text helpers for the MacroFlow event editor., Return the event editor footer summary text., _summary_text(), Event editor summary text helper regression tests., test_summary_text_appends_edited_tag_when_macro_is_edited(), test_summary_text_matches_current_refresh_format_without_edited_tag()

### Community 22 - "Community 22"
Cohesion: 0.32
Nodes (7): _get_favorites_source(), 즐겨찾기 검색 필터 존재 여부 테스트., favorites.py 소스 코드를 직접 읽어 반환한다., FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다., FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다., test_favorites_widget_has_apply_search_filter(), test_favorites_widget_has_search_box_in_setup_ui()

### Community 23 - "Community 23"
Cohesion: 0.33
Nodes (5): mock_hook(), mock_win32(), pytest 공통 픽스처.  win32 모듈을 mock으로 교체하여 Linux 개발 환경에서도 테스트 가능하게 한다., win32 Platform Layer 전체를 Mock으로 대체한다.      Core 레이어 테스트 시 반드시 사용한다., start_hook / stop_hook을 mock으로 대체하고 직접 주입 가능한 큐를 반환한다.      테스트에서 이 큐에 raw 이벤트를

### Community 24 - "Community 24"
Cohesion: 0.53
Nodes (5): GitHub Actions release safety contract., test_ci_uses_locked_dependencies_on_linux_and_windows(), test_release_requires_manual_dispatch(), test_windows_job_runs_source_tests_and_packaged_exe_smoke(), _workflow_text()

### Community 25 - "Community 25"
Cohesion: 0.4
Nodes (4): 일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다., mouse_move 영구 삭제는 확인창을 거쳐야 한다., test_delete_mouse_moves_requires_confirmation_dialog(), test_play_toolbar_uses_stop_copy_while_playing()

### Community 26 - "Community 26"
Cohesion: 0.6
Nodes (4): Real-PyQt subprocess regressions for runtime-only UI paths., _run_offscreen(), test_main_window_shortcut_fallback_uses_real_pyqt_shortcut(), test_sequencer_worker_callbacks_update_visible_state_on_gui_thread()

### Community 27 - "Community 27"
Cohesion: 0.4
Nodes (4): RDP smoke 관련 Linux 계약 테스트 문서는 uv run pytest 형태로 통일한다., CLAUDE 명령 예시는 바깥 active venv와 무관하게 프로젝트 .venv를 사용해야 한다., test_claude_commands_use_project_venv_friendly_uv_run(), test_linux_side_smoke_docs_use_uv_run_pytest()

### Community 28 - "Community 28"
Cohesion: 0.4
Nodes (4): 존재하지 않는 파일은 시퀀서 목록 append 전에 차단해야 한다., 같은 매크로 경로는 중복 append 전에 차단해야 한다., test_add_item_rejects_duplicate_paths_before_append(), test_add_item_rejects_missing_files_before_append()

### Community 29 - "Community 29"
Cohesion: 0.5
Nodes (4): _question_calls_in_start_append_recording(), MainWindow 이어서 녹화 확인창 계약 테스트., 이어서 녹화 확인창은 Space만 눌러도 진행되도록 Yes를 기본 버튼으로 둔다., test_append_recording_confirmation_defaults_to_yes_for_spacebar()

### Community 30 - "Community 30"
Cohesion: 0.4
Nodes (4): 메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다., QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다., test_package_version_matches_project_metadata(), test_qapplication_version_uses_package_version()

### Community 31 - "Community 31"
Cohesion: 0.5
Nodes (3): UI package import boundaries., 순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다., test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()

### Community 32 - "Community 32"
Cohesion: 0.83
Nodes (3): _script_text(), test_runner_preserves_clipboard_summary_contract(), test_runner_redirects_stdout_and_stderr_without_powershell_error_records()

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (2): _load_harness(), test_build_smoke_macro_exercises_windows_input_and_color_wait_paths()

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Return whether a complete repeat-session stop was requested.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Return user-facing repeat cycle label, e.g. '3/10회'.

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0):

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0):

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0):

## Knowledge Gaps
- **168 isolated node(s):** `MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag`, `파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다.`, `Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목.`, `Pure validation rules for MacroFlow condition expressions.  This module owns the`, `Return whether an AST node is statically a numeric expression.` (+163 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 34`** (1 nodes): `Return whether a complete repeat-session stop was requested.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Return user-facing repeat cycle label, e.g. '3/10회'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `run_rdp_runtime_safety_smoke.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `run_rdp_gui_smoke.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MacroData` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 11`, `Community 13`, `Community 16`, `Community 19`?**
  _High betweenness centrality (0.223) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `Community 1` to `Community 0`, `Community 3`, `Community 6`, `Community 13`, `Community 20`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `EventEditorWidget` connect `Community 1` to `Community 0`, `Community 10`, `Community 3`, `Community 15`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 276 inferred relationships involving `MacroData` (e.g. with `_MacroItem` and `MacroSequencerWidget`) actually correct?**
  _`MacroData` has 276 INFERRED edges - model-reasoned connections that need verification._
- **Are the 238 inferred relationships involving `MouseButtonEvent` (e.g. with `_convert_raw()` and `_dict_to_event()`) actually correct?**
  _`MouseButtonEvent` has 238 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `KeyEvent` (e.g. with `_convert_raw()` and `_dict_to_event()`) actually correct?**
  _`KeyEvent` has 177 INFERRED edges - model-reasoned connections that need verification._
- **Are the 177 inferred relationships involving `MacroSettings` (e.g. with `stop_recording()` and `_dict_to_settings()`) actually correct?**
  _`MacroSettings` has 177 INFERRED edges - model-reasoned connections that need verification._