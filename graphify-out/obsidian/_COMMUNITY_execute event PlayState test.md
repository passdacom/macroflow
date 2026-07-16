---
type: community
cohesion: 0.03
members: 130
---

# execute event PlayState test

**Cohesion:** 0.03 - loosely connected
**Members:** 130 nodes

## Members
- [[.mouseMoveEvent()]] - code - ./src/macroflow/ui/overlay.py
- [[.test_black()]] - code - ./tests/test_player.py
- [[.test_boundary()]] - code - ./tests/test_player.py
- [[.test_click_color_check_nudges_cursor_after_one_second()]] - code - ./tests/test_player.py
- [[.test_click_color_check_timeout_zero_waits_until_match()]] - code - ./tests/test_player.py
- [[.test_delay_override_is_scaled_by_playback_speed()]] - code - ./tests/test_player.py
- [[.test_delay_override_respected()]] - code - ./tests/test_player.py
- [[.test_exact_match()]] - code - ./tests/test_player.py
- [[.test_key_down_executes()]] - code - ./tests/test_player.py
- [[.test_key_up_executes()]] - code - ./tests/test_player.py
- [[.test_mixed()]] - code - ./tests/test_player.py
- [[.test_mouse_move_executes()]] - code - ./tests/test_player.py
- [[.test_outside_tolerance()]] - code - ./tests/test_player.py
- [[.test_play_completes()]] - code - ./tests/test_player.py
- [[.test_red()]] - code - ./tests/test_player.py
- [[.test_skip_mode_waits_then_skips_when_color_never_matches()]] - code - ./tests/test_player.py
- [[.test_stop_interrupts_playback()]] - code - ./tests/test_player.py
- [[.test_stop_mode_raises_after_timeout_when_color_never_matches()]] - code - ./tests/test_player.py
- [[.test_stop_mode_waits_for_match_before_stopping()]] - code - ./tests/test_player.py
- [[.test_text_input_calls_send_text()]] - code - ./tests/test_player.py
- [[.test_text_input_empty_string()]] - code - ./tests/test_player.py
- [[.test_wait_event_compensates_following_timeline()]] - code - ./tests/test_player.py
- [[.test_wait_event_duration_is_scaled_by_playback_speed()]] - code - ./tests/test_player.py
- [[.test_wait_event_sleeps()]] - code - ./tests/test_player.py
- [[.test_wait_mode_polls_until_match()]] - code - ./tests/test_player.py
- [[.test_white()]] - code - ./tests/test_player.py
- [[.test_within_tolerance()]] - code - ./tests/test_player.py
- [[GetPixel로 단일 픽셀 RGB 값을 반환한다.      core-beliefs.md 원칙 7 스크린샷 API 금지 — GetPixel만]] - rationale - ./src/macroflow/win32/hooks.py
- [[LoopEvent의 events 배열을 지정 횟수만큼 반복 실행한다.      Args         event 실행할 LoopEvent.]] - rationale - ./src/macroflow/script_engine.py
- [[TestColorCheckWait]] - code - ./tests/test_player.py
- [[TestColorMatches]] - code - ./tests/test_player.py
- [[TestExecuteEvent]] - code - ./tests/test_player.py
- [[TestHexToRgb]] - code - ./tests/test_player.py
- [[TestPlaybackTiming]] - code - ./tests/test_player.py
- [[Unicode 문자열을 KEYEVENTF_UNICODE로 문자 단위 전송한다.      키보드 배치·IME 상태에 무관하게 입력한 문자를 그대로]] - rationale - ./src/macroflow/win32/sendinput.py
- [[Win32 SendInput API 래퍼.  마우스 이동·클릭·드래그, 키보드 입력을 원자적으로 전송한다. MOUSEEVENTF_ABSOLUTE]] - rationale - ./src/macroflow/win32/sendinput.py
- [[_HARDWAREINPUT]] - code - ./src/macroflow/win32/sendinput.py
- [[_INPUT]] - code - ./src/macroflow/win32/sendinput.py
- [[_INPUT_UNION]] - code - ./src/macroflow/win32/sendinput.py
- [[_KEYBDINPUT]] - code - ./src/macroflow/win32/sendinput.py
- [[_MOUSEINPUT]] - code - ./src/macroflow/win32/sendinput.py
- [[_PlayState]] - code - ./src/macroflow/player.py
- [[_color_check_timeout_ms_for_action()]] - code - ./src/macroflow/player.py
- [[_color_matches()_1]] - code - ./src/macroflow/player.py
- [[_event_timing_compensation_ns()]] - code - ./src/macroflow/player.py
- [[_execute_event()]] - code - ./src/macroflow/player.py
- [[_execute_event_sequence()]] - code - ./src/macroflow/player.py
- [[_hex_to_rgb()_1]] - code - ./src/macroflow/player.py
- [[_make_macro()_3]] - code - ./tests/test_player.py
- [[_make_macro()_1]] - code - ./tests/test_player_runtime_safety.py
- [[_mouse_input()]] - code - ./src/macroflow/win32/sendinput.py
- [[_normalize()]] - code - ./src/macroflow/win32/sendinput.py
- [[_nudge_cursor_if_due()]] - code - ./src/macroflow/player.py
- [[_play_loop()]] - code - ./src/macroflow/player.py
- [[_reset_player()]] - code - ./tests/test_player_runtime_safety.py
- [[_run_offscreen()_1]] - code - ./tests/test_functional_audit_regressions.py
- [[_send()]] - code - ./src/macroflow/win32/sendinput.py
- [[_wait_for_click_color_check()]] - code - ./src/macroflow/player.py
- [[_wait_for_color()]] - code - ./src/macroflow/player.py
- [[_wait_for_color_check()]] - code - ./src/macroflow/player.py
- [[_wait_for_window()]] - code - ./src/macroflow/player.py
- [[execute_loop()]] - code - ./src/macroflow/script_engine.py
- [[find_window()_1]] - code - ./src/macroflow/win32/hooks.py
- [[get_current_event_idx()]] - code - ./src/macroflow/player.py
- [[get_pixel_color()_1]] - code - ./src/macroflow/win32/hooks.py
- [[get_progress()]] - code - ./src/macroflow/player.py
- [[legacy timeout은 per-action timeout이 모두 기본값일 때만 사용한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[legacy 단일 timeout만 설정한 기존 호출 경로도 기존 값으로 동작해야 한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[mock_win32()_1]] - code - ./tests/test_player.py
- [[pause()]] - code - ./src/macroflow/player.py
- [[play()]] - code - ./src/macroflow/player.py
- [[player.py]] - code - ./src/macroflow/player.py
- [[resume()]] - code - ./src/macroflow/player.py
- [[send_key()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[send_mouse_button()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[send_mouse_click()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[send_mouse_drag()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[send_mouse_move()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[send_mouse_wheel()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[send_text()_1]] - code - ./src/macroflow/win32/sendinput.py
- [[sendinput.py]] - code - ./src/macroflow/win32/sendinput.py
- [[stop()]] - code - ./src/macroflow/player.py
- [[test_click_color_check_has_independent_timeout_defaults_per_action()]] - code - ./tests/test_color_settings_regressions.py
- [[test_click_color_timeout_does_not_overshoot_poll_interval()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_color_check_mouse_down_wait_time_compensates_following_event_timestamps()]] - code - ./tests/test_color_settings_regressions.py
- [[test_color_settings_regressions.py]] - code - ./tests/test_color_settings_regressions.py
- [[test_delay_override_shifts_following_timestamp_and_preserves_click()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_emergency_hook_failure_keeps_playback_idle()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_event_range_progress_is_relative_and_bounded()]] - code - ./tests/test_player_runtime_safety.py
- [[test_external_color_settings_are_normalized_at_load_boundary()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_flow_overlay_lifecycle_and_sequencer_progress_signal()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_functional_audit_regressions.py]] - code - ./tests/test_functional_audit_regressions.py
- [[test_loop_nested_delay_override_uses_scheduler_and_speed()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_macro_color_trigger_clamps_non_positive_poll_interval()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_main_window_persists_color_settings_in_qsettings_contract()]] - code - ./tests/test_color_settings_regressions.py
- [[test_overlay_expands_for_max_repeat_without_clipping()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_overlay_start_methods_force_visible_on_top_contract()]] - code - ./tests/test_color_settings_regressions.py
- [[test_plain_mouse_down_does_not_compensate_timestamps()]] - code - ./tests/test_color_settings_regressions.py
- [[test_play_allows_terminal_worker_handoff()]] - code - ./tests/test_player_runtime_safety.py
- [[test_play_rejects_overlapping_worker()]] - code - ./tests/test_player_runtime_safety.py
- [[test_player.py]] - code - ./tests/test_player.py
- [[test_player_does_not_use_legacy_for_only_one_non_default_action()]] - code - ./tests/test_color_settings_regressions.py
- [[test_player_runtime_safety.py]] - code - ./tests/test_player_runtime_safety.py
- [[test_player_selects_timeout_by_color_check_action()]] - code - ./tests/test_color_settings_regressions.py
- [[test_player_start_failure_restores_idle_overlay_state()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_player_uses_legacy_click_color_timeout_when_action_timeouts_are_default()]] - code - ./tests/test_color_settings_regressions.py
- [[test_recorded_relative_time_does_not_mix_in_playback_override()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_regular_operations_are_blocked_while_sequence_runs()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_sequence_start_is_blocked_while_regular_operation_runs()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_sequencer_generation_stop_timeout_and_mutation_guards()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_stop_during_color_read_prevents_mouse_down()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_stop_interrupts_scheduled_gap_before_next_input()]] - code - ./tests/test_player_runtime_safety.py
- [[test_stop_interrupts_wait_event_without_post_stop_callback()]] - code - ./tests/test_player_runtime_safety.py
- [[test_time_headers_name_recorded_time_and_playback_wait()]] - code - ./tests/test_functional_audit_regressions.py
- [[test_user_stop_during_click_color_wait_does_not_emit_mismatch_error()]] - code - ./tests/test_player_runtime_safety.py
- [[title_contains를 제목에 포함하는 창 핸들(HWND)을 반환한다.      Args         title_contains 검색]] - rationale - ./src/macroflow/win32/hooks.py
- [[x1,y1 → x2,y2 직선 드래그를 전송한다 (down + 보간 이동 + up).      10단계로 보간하여 자연스러운 드래그를 재현한다.]] - rationale - ./src/macroflow/win32/sendinput.py
- [[가상 키 코드로 키 이벤트(down 또는 up)를 전송한다.      Args         vk_code Windows Virtual Ke]] - rationale - ./src/macroflow/win32/sendinput.py
- [[대기무시중지 동작은 각자 독립 timeout 기본값을 가져야 한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[마우스 버튼 단독 이벤트(down 또는 up만)를 전송한다.      send_mouse_click과 달리 downup 중 하나만 전송한다.]] - rationale - ./src/macroflow/win32/sendinput.py
- [[색 설정은 매크로 파일 저장 없이도 앱 설정으로 저장복원되어야 한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[색 체크 timeout 세분화지속성 회귀 테스트.]] - rationale - ./tests/test_color_settings_regressions.py
- [[색 체크 대기 시간이 끼어도 다음 이벤트들이 과거 target으로 몰려 급가속하지 않아야 한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[일반 녹화재생 오버레이도 hint처럼 위치 재설정+showraiseupdate 경로를 타야 한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[일반 클릭에는 인위적인 timestamp 보정을 넣지 않는다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[지정 좌표에서 마우스 클릭(down + up)을 원자적으로 전송한다.      Args         x 클릭 X 좌표 (픽셀).]] - rationale - ./src/macroflow/win32/sendinput.py
- [[커서를 절대 픽셀 좌표로 이동한다.      Args         x 목표 X 좌표 (픽셀).         y 목표 Y 좌표 (픽셀).]] - rationale - ./src/macroflow/win32/sendinput.py
- [[커서를 지정 위치로 이동한 뒤 휠 스크롤 이벤트를 전송한다.      커서를 먼저 이동해야 올바른 윈도우가 이벤트를 수신한다.     delta]] - rationale - ./src/macroflow/win32/sendinput.py
- [[클릭 색 체크 runtime은 이벤트의 mismatch action별 timeout을 선택해야 한다.]] - rationale - ./tests/test_color_settings_regressions.py
- [[픽셀 좌표를 SendInput ABSOLUTE 모드 좌표 (0~65535)로 변환한다.]] - rationale - ./src/macroflow/win32/sendinput.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/execute_event_PlayState_test
SORT file.name ASC
```

## Connections to other communities
- 185 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 13 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 7 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 7 edges to [[_COMMUNITY_mock.py hooks.py get logical]]
- 4 edges to [[_COMMUNITY_build rows editor rows.py]]
- 3 edges to [[_COMMUNITY_test macro file.py load]]
- 2 edges to [[_COMMUNITY_rdp runtime safety smoke.py]]
- 2 edges to [[_COMMUNITY_convert raw TestConvertRaw recorder.py]]
- 1 edge to [[_COMMUNITY_test expression sandbox module.py]]
- 1 edge to [[_COMMUNITY_append recording test append]]
- 1 edge to [[_COMMUNITY_EventEditorWidget add single row]]

## Top bridge nodes
- [[.mouseMoveEvent()]] - degree 21, connects to 7 communities
- [[get_pixel_color()_1]] - degree 10, connects to 4 communities
- [[_execute_event()]] - degree 30, connects to 3 communities
- [[test_functional_audit_regressions.py]] - degree 23, connects to 3 communities
- [[play()]] - degree 17, connects to 3 communities