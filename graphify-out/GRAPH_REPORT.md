# Graph Report - /root/.openclaw/workspace/macroflow-ui-followup  (2026-07-29)

## Corpus Check
- 115 files · ~119,385 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2697 nodes · 13948 edges · 95 communities detected
- Extraction: 22% EXTRACTED · 78% INFERRED · 0% AMBIGUOUS · INFERRED: 10884 edges (avg confidence: 0.54)
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
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]

## God Nodes (most connected - your core abstractions)
1. `MacroData` - 862 edges
2. `MouseButtonEvent` - 705 edges
3. `MacroSettings` - 659 edges
4. `TextInputEvent` - 606 edges
5. `ColorTriggerEvent` - 596 edges
6. `KeyEvent` - 535 edges
7. `MouseMoveEvent` - 526 edges
8. `MouseWheelEvent` - 462 edges
9. `WaitEvent` - 437 edges
10. `ConditionEvent` - 424 edges

## Surprising Connections (you probably didn't know these)
- `MacroData` --uses--> `Undo/history helpers for the MacroFlow event editor.  This module is intentional`  [INFERRED]
  /root/.openclaw/workspace/macroflow-ui-followup/src/macroflow/types.py → ./src/macroflow/ui/editor_history.py
- `MacroData` --uses--> `Return a deep copy suitable for undo/redo snapshots.`  [INFERRED]
  /root/.openclaw/workspace/macroflow-ui-followup/src/macroflow/types.py → ./src/macroflow/ui/editor_history.py
- `MacroData` --uses--> `Return a MacroData copy with a replaced event list.      Metadata, settings, and`  [INFERRED]
  /root/.openclaw/workspace/macroflow-ui-followup/src/macroflow/types.py → ./src/macroflow/ui/editor_history.py
- `MacroData` --uses--> `Helpers for appending a fresh recording to an existing macro.  This module is in`  [INFERRED]
  /root/.openclaw/workspace/macroflow-ui-followup/src/macroflow/types.py → ./src/macroflow/ui/append_recording.py
- `MacroData` --uses--> `Return copies of ``events`` shifted so the first event starts at a timestamp.`  [INFERRED]
  /root/.openclaw/workspace/macroflow-ui-followup/src/macroflow/types.py → ./src/macroflow/ui/append_recording.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (657): Pure event insertion helpers for the MacroFlow event editor.  This module intent, Return events with click or double-click MouseButtonEvents inserted., Return events with one configured ColorTriggerEvent inserted., Return the source event index after which an editor insertion should occur., Insert events after an index and shift following timestamps to preserve timing., Return events with one TextInputEvent inserted and later timestamps shifted., MacroFlow 이벤트 에디터 위젯.  그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력. Undo/Redo,, 휠 이벤트(그룹)의 스크롤 양과 방향을 변경한다.          그룹 전체를 단일 이벤트로 병합 후 delta를 적용한다.         이렇 (+649 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (275): EventEditorWidget, FavoritesWidget, 즐겨찾기 트리 위젯.      favorites/ 디렉토리와 _index.json 파일을 함께 관리한다.     새로 추가된 항목은 기본 그룹(, 즐겨찾기 디렉토리를 설정하고 트리를 초기 로드한다., MacroData를 즐겨찾기 폴더에 저장하고 기본 그룹에 추가한다.          Args:             macro_data: 저장할, _index.json 을 읽어 self._index 에 적재한다., self._index 를 _index.json 에 저장한다., 기본 그룹이 없으면 인덱스 맨 앞에 생성한다. (+267 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (117): Exception, 검색어에 따라 트리 항목 표시/숨김을 적용한다.          검색어가 비어있으면 모두 표시.         검색어가 있으면 이름에 검색어(대, User-facing help text kept separate from Qt dialogs for regression testing., _emg_keyboard_proc(), _emg_pump(), get_cursor_pos(), _KBDLLHOOKSTRUCT, _keyboard_proc() (+109 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (250): Side-effect-free runtime smokes used by packaged Windows artifacts., Exercise packaged mixed-sequence imports and codecs without sending input., run_inline_sequence_smoke(), _color_matches(), ColorCheckNode, _dict_to_node(), EndNode, _flow_to_dict() (+242 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (117): create_capture_controls(), create_delay_spin(), create_percentage_spin(), Small widget factories shared by MacroFlow editor dialogs., Create a position percentage spin box with the editor's shared bounds., Create a millisecond delay spin box with the editor's shared suffix., Create the standard F6 capture label/button pair used in editor dialogs., copy_events() (+109 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (118): Win32 clipboard writes for user-confirmed macro text.  This module never reads o, Replace the clipboard with ``text`` without reading prior clipboard data., set_clipboard_text(), get_dpi_scale(), get_logical_screen_size(), pixel_to_ratio(), ratio_to_pixel(), Win32 DPI 스케일링 처리.  논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다. 모듈 임포트 시 SetProcessDpiAware (+110 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (78): _atomic_backup(), _bounded_int(), delete_mouse_moves(), _dict_to_settings(), edit_key_value(), edit_position(), edit_wheel_delta(), event_from_dict() (+70 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (33): _check_esc_triple(), configure_filtered_hotkey_vk_codes(), _consumer_loop(), _convert_raw(), filtered_hotkey_vk_codes(), get_event_count(), inject_color_trigger(), inject_text_input() (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (46): arm_hotkey_config_recovery(), canonicalize_hotkey(), _canonicalize_if_possible(), disarm_hotkey_config_recovery(), HotkeySpec, HotkeyValidationResult, load_hotkey_config(), _parse_chord() (+38 more)

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (48): _apply_row_metadata(), _build_color_trigger_row(), _build_condition_row(), _build_key_down_row(), _build_key_up_row(), _build_loop_row(), _build_mouse_down_row(), _build_mouse_move_row() (+40 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (29): _click_events(), main(), parse_args(), _ratio(), run_gui_smoke(), append_event(), build_assertions(), initial_status() (+21 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (31): append_recording(), Helpers for appending a fresh recording to an existing macro.  This module is in, Return copies of ``events`` shifted so the first event starts at a timestamp., Append a newly recorded macro to ``base_macro`` and return a new MacroData., shift_event_timestamps(), delete_after_group(), range_from_group_to_end(), Pure editor tail-action helpers. (+23 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (17): find_window(), get_cursor_pos(), get_foreground_window(), get_logical_screen_size(), get_pixel_color(), is_foreground_window(), Win32 Mock 구현 — Linux/개발 환경용.  openclaw 같은 Linux 서버에서 Claude Code가 작업할 때 자동으로 사용, GetSystemMetrics Mock — 기본 1920×1080. (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.1
Nodes (23): _is_numeric_expression(), Pure validation rules for MacroFlow condition expressions.  This module owns the, Return whether an AST node is statically a numeric expression., Validate a sandbox wait value and return milliseconds as a float., Validate that an expression contains only the permitted AST surface., validate_expression(), validate_wait_ms(), execute_condition() (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.19
Nodes (19): Real-PyQt subprocess regressions for runtime-only UI paths., _run_offscreen(), test_f9_final_focus_failure_keeps_recording_paused(), test_f9_quick_text_pauses_during_dialog_and_resumes_after_target_input(), test_f9_quick_text_preserves_existing_pause_ownership(), test_f9_send_failure_does_not_commit_text_event(), test_f9_session_blocks_f8_resume_and_nested_f9(), test_f9_text_delay_settings_persists_app_default_without_macro() (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (14): _FakeFunction, _FakeUser32, Win32 foreground-window helper contract tests., test_activate_with_user32_rejects_invalid_handle(), test_activate_with_user32_shows_and_raises_without_topmost_state(), _activate_with_user32(), bring_window_to_foreground(), get_foreground_window() (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.2
Nodes (10): _FakeWidget, _import_editor(), _install_fake_pyqt(), _make_widget(), Event editor F6 capture lifecycle behavior with Qt mocked out., _Signal, test_cancel_f6_capture_only_emits_when_active(), test_consume_f6_capture_runs_once_and_emits_end() (+2 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (13): move_filenames_to_group(), Pure helpers for Favorites batch actions.  The Favorites UI itself is PyQt-based, Return path names in first-seen order, dropping duplicates and blanks., Move filenames to a target group in-place without duplicating items., Remove filenames from every group in-place., remove_filenames_from_groups(), unique_filenames(), _index() (+5 more)

### Community 18 - "Community 18"
Cohesion: 0.29
Nodes (10): main(), _next_version(), Validate all version sources, then update them to one computed version., update_versions(), _load_bump_module(), Version bump automation tests., _read_declared_versions(), test_update_versions_rejects_mismatch_without_writing() (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.36
Nodes (7): Headless contracts for heterogeneous sequencer steps., _run_qt(), test_f6_capture_creates_actions_and_duplicate_gets_new_identity(), test_mixed_steps_save_load_duplicate_paths_and_preflight(), test_modal_reentry_cannot_commit_sequence_or_file_mutations(), test_preflight_failure_and_running_edit_locks_are_truthful(), test_step_reorder_uses_step_id_not_duplicate_path()

### Community 20 - "Community 20"
Cohesion: 0.39
Nodes (8): 시퀀서 미저장 변경 보호 회귀 테스트.  기존 일부 테스트가 collection 시점에 PyQt 모듈을 대체하므로 실제 Qt 검증은 독립 sub, _run_offscreen(), test_dirty_transitions_for_mutations_and_noops(), test_linear_flow_with_noncanonical_document_data_is_rejected(), test_lossy_flow_projection_is_rejected(), test_main_window_dirty_tab_and_close_cancel(), test_save_load_and_save_as_failure_are_transactional(), test_unsaved_prompt_and_failed_open_preserve_state()

### Community 21 - "Community 21"
Cohesion: 0.32
Nodes (7): _get_favorites_source(), 즐겨찾기 검색 필터 존재 여부 테스트., favorites.py 소스 코드를 직접 읽어 반환한다., FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다., FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다., test_favorites_widget_has_apply_search_filter(), test_favorites_widget_has_search_box_in_setup_ui()

### Community 22 - "Community 22"
Cohesion: 0.43
Nodes (7): Real-Qt contracts for contextual MacroFlow toolbar layout and document routing., _run_offscreen(), test_ctrl_s_routes_to_active_document_surface_only(), test_playback_spinboxes_show_their_largest_values_without_clipping(), test_toolbar_rows_fit_initial_width_without_restricting_manual_shrink(), test_toolbar_rows_stay_fixed_and_tab_actions_align(), test_toolbars_can_be_widened_to_fit_larger_accessibility_font()

### Community 23 - "Community 23"
Cohesion: 0.43
Nodes (7): Real-Qt tests for configurable shortcut adapters and dialog validation., _run_offscreen(), test_hotkey_dialog_rejects_duplicate_candidate_and_restores_defaults(), test_hotkey_dialog_uses_localized_confirmation_buttons(), test_qsettings_hotkey_config_round_trip_is_durable(), test_qt_focused_bindings_replace_without_active_stale_shortcuts(), test_quick_text_dialog_title_uses_configured_trigger_key()

### Community 24 - "Community 24"
Cohesion: 0.5
Nodes (7): GitHub Actions release safety contract., _steps(), test_actions_are_sha_pinned_and_tokens_are_least_privilege(), test_ci_uses_locked_dependencies_on_linux_and_windows(), test_release_requires_manual_dispatch_and_publishes_provenance(), test_windows_job_runs_tests_before_build_and_owns_smoke_process_tree(), _workflow()

### Community 25 - "Community 25"
Cohesion: 0.33
Nodes (5): mock_hook(), mock_win32(), pytest 공통 픽스처.  win32 모듈을 mock으로 교체하여 Linux 개발 환경에서도 테스트 가능하게 한다., win32 Platform Layer 전체를 Mock으로 대체한다.      Core 레이어 테스트 시 반드시 사용한다., start_hook / stop_hook을 mock으로 대체하고 직접 주입 가능한 큐를 반환한다.      테스트에서 이 큐에 raw 이벤트를

### Community 26 - "Community 26"
Cohesion: 0.6
Nodes (4): MainWindow integration contracts for transactional hotkey settings., _run_offscreen(), test_main_window_persists_and_updates_recorder_only_after_successful_apply(), test_modal_hotkey_settings_blocks_runtime_dispatch_and_rechecks_idle_state()

### Community 27 - "Community 27"
Cohesion: 0.4
Nodes (4): RDP smoke 관련 Linux 계약 테스트 문서는 uv run pytest 형태로 통일한다., CLAUDE 명령 예시는 바깥 active venv와 무관하게 프로젝트 .venv를 사용해야 한다., test_claude_commands_use_project_venv_friendly_uv_run(), test_linux_side_smoke_docs_use_uv_run_pytest()

### Community 28 - "Community 28"
Cohesion: 0.6
Nodes (4): Real-Qt regressions for focusing newly inserted editor actions., _run_offscreen(), test_async_color_insert_aborts_if_editor_model_changed_during_capture(), test_inserted_editor_row_becomes_selection_focus_and_next_anchor()

### Community 29 - "Community 29"
Cohesion: 0.4
Nodes (4): 존재하지 않는 파일은 시퀀서 목록 append 전에 차단해야 한다., 같은 매크로 파일을 여러 단계에서 의도적으로 재실행할 수 있어야 한다., test_add_item_allows_duplicate_paths_as_distinct_steps(), test_add_item_rejects_missing_files_before_insert()

### Community 30 - "Community 30"
Cohesion: 0.5
Nodes (4): _question_calls_in_start_append_recording(), MainWindow 이어서 녹화 확인창 계약 테스트., 이어서 녹화 확인창은 Space만 눌러도 진행되도록 Yes를 기본 버튼으로 둔다., test_append_recording_confirmation_defaults_to_yes_for_spacebar()

### Community 31 - "Community 31"
Cohesion: 0.4
Nodes (4): 메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다., QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다., test_package_version_matches_project_metadata(), test_qapplication_version_uses_package_version()

### Community 32 - "Community 32"
Cohesion: 0.5
Nodes (1): Playback-delay help content and menu accessibility contracts.

### Community 33 - "Community 33"
Cohesion: 0.5
Nodes (3): UI package import boundaries., 순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다., test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()

### Community 34 - "Community 34"
Cohesion: 0.83
Nodes (3): _script_text(), test_runner_preserves_clipboard_summary_contract(), test_runner_redirects_stdout_and_stderr_without_powershell_error_records()

### Community 35 - "Community 35"
Cohesion: 0.67
Nodes (1): Real-Qt contracts for interactive editor column redistribution.

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (2): _load_harness(), test_build_smoke_macro_exercises_windows_input_and_color_wait_paths()

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Return whether a complete repeat-session stop was requested.

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Return user-facing repeat cycle label, e.g. '3/10회'.

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0):

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0):

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0):

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (1): 즐겨찾기 디렉토리를 설정하고 트리를 초기 로드한다.

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (1): MacroData를 즐겨찾기 폴더에 저장하고 기본 그룹에 추가한다.          Args:             macro_data: 저장할

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (1): _index.json 을 읽어 self._index 에 적재한다.

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (1): self._index 를 _index.json 에 저장한다.

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): 기본 그룹이 없으면 인덱스 맨 앞에 생성한다.

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): 인덱스에 등록된 모든 파일명 집합을 반환한다.

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): 검색어에 따라 트리 항목 표시/숨김을 적용한다.          검색어가 비어있으면 모두 표시.         검색어가 있으면 이름에 검색어(대

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): 현재 선택된 즐겨찾기 item들의 경로를 트리 순서대로 반환한다.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): 현재 선택된 즐겨찾기 item들의 파일명을 중복 없이 반환한다.

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): 그룹 펼침/접힘 상태를 인덱스에 즉시 반영한다.

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): 드래그앤드롭 완료 후 트리 순서를 인덱스에 반영한다.

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): 다중 선택된 즐겨찾기 항목의 일괄 작업 메뉴를 구성한다.

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): 선택된 즐겨찾기 항목들을 현재 트리 선택 순서대로 시퀀서에 추가한다.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): 선택된 즐겨찾기 항목들을 지정 그룹으로 일괄 이동한다.

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): 즐겨찾기 항목의 이름을 변경하고 실제 파일도 rename한다.          인덱스의 filename과 파일 경로를 동시에 업데이트한다.

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): 여러 즐겨찾기 항목을 한 번의 확인 후 인덱스와 파일 시스템에서 제거한다.

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): 파일명으로 사용할 수 없는 문자를 제거하고 안전한 이름을 반환한다.

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): FindWindow Mock — 항상 None 반환.

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): GetSystemMetrics Mock — 기본 1920×1080.

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (1): 픽셀 좌표를 SendInput ABSOLUTE 모드 좌표 (0~65535)로 변환한다.

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): 커서를 절대 픽셀 좌표로 이동한다.      Args:         x: 목표 X 좌표 (픽셀).         y: 목표 Y 좌표 (픽셀).

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): x1,y1 → x2,y2 직선 드래그를 전송한다 (down + 보간 이동 + up).      10단계로 보간하여 자연스러운 드래그를 재현한다.

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (1): 마우스 버튼 단독 이벤트(down 또는 up만)를 전송한다.      send_mouse_click과 달리 down/up 중 하나만 전송한다.

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): 커서를 지정 위치로 이동한 뒤 휠 스크롤 이벤트를 전송한다.      커서를 먼저 이동해야 올바른 윈도우가 이벤트를 수신한다.     delta

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): 가상 키 코드로 키 이벤트(down 또는 up)를 전송한다.      Args:         vk_code: Windows Virtual Ke

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Unicode 문자열을 KEYEVENTF_UNICODE로 문자 단위 전송한다.      키보드 배치·IME 상태에 무관하게 입력한 문자를 그대로

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): 마우스 Low-Level Hook 이벤트 구조체.

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (1): 키보드 Low-Level Hook 이벤트 구조체.

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (1): 마우스 LL Hook 콜백 — 최소 처리 후 즉시 반환.

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (1): 키보드 LL Hook 콜백 — 최소 처리 후 즉시 반환.

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): 긴급 중지 전용 키보드 LL Hook 콜백.

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (1): WH_MOUSE_LL + WH_KEYBOARD_LL을 단일 스레드에서 처리하는 메시지 펌프.      WM_QUIT 수신 시 Hook 해제 후

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): WH_KEYBOARD_LL (긴급 중지 전용) 메시지 펌프.

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (1): Hook을 등록하고 메시지 펌프 스레드를 시작한다.      Args:         queue: 캡처된 원시 이벤트를 쌓을 deque.

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): WM_QUIT을 펌프 스레드에 보내 Hook을 해제하고 스레드를 종료한다.

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): 재생 중 ESC×3 긴급 중지 감지용 키보드 Hook을 시작한다.      LLKHF_INJECTED 이벤트(SendInput 주입)는 무시하므

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (1): 긴급 중지 Hook을 해제하고 스레드를 종료한다.

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): GetPixel로 단일 픽셀 RGB 값을 반환한다.      core-beliefs.md 원칙 7: 스크린샷 API 금지 — GetPixel만

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): 현재 마우스 커서의 화면 좌표(픽셀)를 반환한다.      Returns:         (x, y) 픽셀 좌표 튜플.

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): title_contains를 제목에 포함하는 창 핸들(HWND)을 반환한다.      Args:         title_contains: 검색

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): 일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다.

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): mouse_move 영구 삭제는 확인창을 거쳐야 한다.

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (1): 텍스트가 잘리지 않게 폭을 늘리고 표시 중이면 오른쪽 끝 위치를 유지한다.

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): 오버레이를 현재 화면 우하단에 다시 배치하고 최상단으로 표시한다.

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): 시퀀스/플로우 실행 모드로 오버레이를 표시한다.

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): 재생 진행률(0.0~1.0)을 갱신한다.

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): 시퀀스의 현재/전체 매크로 순번을 갱신한다.

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): F6 캡처 대기 중 힌트 메시지를 표시한다.

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (1): F6 캡처 대기 힌트 메시지를 그린다.

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (1): FindWindow Mock — 항상 None 반환.

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (1): GetSystemMetrics Mock — 기본 1920×1080.

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (1): mouse_move 영구 삭제는 확인창을 거쳐야 한다.

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (1): 같은 매크로 경로는 중복 append 전에 차단해야 한다.

## Knowledge Gaps
- **270 isolated node(s):** `MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag`, `파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다.`, `Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목.`, `Pure validation rules for MacroFlow condition expressions.  This module owns the`, `Return whether an AST node is statically a numeric expression.` (+265 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 37`** (1 nodes): `Return whether a complete repeat-session stop was requested.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Return user-facing repeat cycle label, e.g. '3/10회'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `run_rdp_runtime_safety_smoke.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `run_rdp_gui_smoke.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `즐겨찾기 디렉토리를 설정하고 트리를 초기 로드한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `MacroData를 즐겨찾기 폴더에 저장하고 기본 그룹에 추가한다.          Args:             macro_data: 저장할`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `_index.json 을 읽어 self._index 에 적재한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `self._index 를 _index.json 에 저장한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `기본 그룹이 없으면 인덱스 맨 앞에 생성한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `인덱스에 등록된 모든 파일명 집합을 반환한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `검색어에 따라 트리 항목 표시/숨김을 적용한다.          검색어가 비어있으면 모두 표시.         검색어가 있으면 이름에 검색어(대`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `현재 선택된 즐겨찾기 item들의 경로를 트리 순서대로 반환한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `현재 선택된 즐겨찾기 item들의 파일명을 중복 없이 반환한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `그룹 펼침/접힘 상태를 인덱스에 즉시 반영한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `드래그앤드롭 완료 후 트리 순서를 인덱스에 반영한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `다중 선택된 즐겨찾기 항목의 일괄 작업 메뉴를 구성한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `선택된 즐겨찾기 항목들을 현재 트리 선택 순서대로 시퀀서에 추가한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `선택된 즐겨찾기 항목들을 지정 그룹으로 일괄 이동한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `즐겨찾기 항목의 이름을 변경하고 실제 파일도 rename한다.          인덱스의 filename과 파일 경로를 동시에 업데이트한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `여러 즐겨찾기 항목을 한 번의 확인 후 인덱스와 파일 시스템에서 제거한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `파일명으로 사용할 수 없는 문자를 제거하고 안전한 이름을 반환한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `FindWindow Mock — 항상 None 반환.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `GetSystemMetrics Mock — 기본 1920×1080.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `픽셀 좌표를 SendInput ABSOLUTE 모드 좌표 (0~65535)로 변환한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `커서를 절대 픽셀 좌표로 이동한다.      Args:         x: 목표 X 좌표 (픽셀).         y: 목표 Y 좌표 (픽셀).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `x1,y1 → x2,y2 직선 드래그를 전송한다 (down + 보간 이동 + up).      10단계로 보간하여 자연스러운 드래그를 재현한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `마우스 버튼 단독 이벤트(down 또는 up만)를 전송한다.      send_mouse_click과 달리 down/up 중 하나만 전송한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `커서를 지정 위치로 이동한 뒤 휠 스크롤 이벤트를 전송한다.      커서를 먼저 이동해야 올바른 윈도우가 이벤트를 수신한다.     delta`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `가상 키 코드로 키 이벤트(down 또는 up)를 전송한다.      Args:         vk_code: Windows Virtual Ke`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Unicode 문자열을 KEYEVENTF_UNICODE로 문자 단위 전송한다.      키보드 배치·IME 상태에 무관하게 입력한 문자를 그대로`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `마우스 Low-Level Hook 이벤트 구조체.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `키보드 Low-Level Hook 이벤트 구조체.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `마우스 LL Hook 콜백 — 최소 처리 후 즉시 반환.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `키보드 LL Hook 콜백 — 최소 처리 후 즉시 반환.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `긴급 중지 전용 키보드 LL Hook 콜백.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `WH_MOUSE_LL + WH_KEYBOARD_LL을 단일 스레드에서 처리하는 메시지 펌프.      WM_QUIT 수신 시 Hook 해제 후`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `WH_KEYBOARD_LL (긴급 중지 전용) 메시지 펌프.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `Hook을 등록하고 메시지 펌프 스레드를 시작한다.      Args:         queue: 캡처된 원시 이벤트를 쌓을 deque.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `WM_QUIT을 펌프 스레드에 보내 Hook을 해제하고 스레드를 종료한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `재생 중 ESC×3 긴급 중지 감지용 키보드 Hook을 시작한다.      LLKHF_INJECTED 이벤트(SendInput 주입)는 무시하므`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `긴급 중지 Hook을 해제하고 스레드를 종료한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `GetPixel로 단일 픽셀 RGB 값을 반환한다.      core-beliefs.md 원칙 7: 스크린샷 API 금지 — GetPixel만`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `현재 마우스 커서의 화면 좌표(픽셀)를 반환한다.      Returns:         (x, y) 픽셀 좌표 튜플.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `title_contains를 제목에 포함하는 창 핸들(HWND)을 반환한다.      Args:         title_contains: 검색`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `mouse_move 영구 삭제는 확인창을 거쳐야 한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `텍스트가 잘리지 않게 폭을 늘리고 표시 중이면 오른쪽 끝 위치를 유지한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `오버레이를 현재 화면 우하단에 다시 배치하고 최상단으로 표시한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `시퀀스/플로우 실행 모드로 오버레이를 표시한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `재생 진행률(0.0~1.0)을 갱신한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `시퀀스의 현재/전체 매크로 순번을 갱신한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `F6 캡처 대기 중 힌트 메시지를 표시한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `F6 캡처 대기 힌트 메시지를 그린다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `FindWindow Mock — 항상 None 반환.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `GetSystemMetrics Mock — 기본 1920×1080.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `mouse_move 영구 삭제는 확인창을 거쳐야 한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `같은 매크로 경로는 중복 append 전에 차단해야 한다.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MacroData` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 11`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Why does `MacroSequencerWidget` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `MouseButtonEvent` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 9`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 860 inferred relationships involving `MacroData` (e.g. with `Pure conversion of heterogeneous sequencer rows into one editable macro.` and `Merge sequence rows without mutating their files, settings, or events.      The`) actually correct?**
  _`MacroData` has 860 INFERRED edges - model-reasoned connections that need verification._
- **Are the 702 inferred relationships involving `MouseButtonEvent` (e.g. with `Side-effect-free runtime smokes used by packaged Windows artifacts.` and `Exercise packaged mixed-sequence imports and codecs without sending input.`) actually correct?**
  _`MouseButtonEvent` has 702 INFERRED edges - model-reasoned connections that need verification._
- **Are the 657 inferred relationships involving `MacroSettings` (e.g. with `Side-effect-free runtime smokes used by packaged Windows artifacts.` and `Exercise packaged mixed-sequence imports and codecs without sending input.`) actually correct?**
  _`MacroSettings` has 657 INFERRED edges - model-reasoned connections that need verification._
- **Are the 603 inferred relationships involving `TextInputEvent` (e.g. with `Side-effect-free runtime smokes used by packaged Windows artifacts.` and `Exercise packaged mixed-sequence imports and codecs without sending input.`) actually correct?**
  _`TextInputEvent` has 603 INFERRED edges - model-reasoned connections that need verification._