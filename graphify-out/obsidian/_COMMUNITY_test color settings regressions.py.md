---
type: community
cohesion: 0.12
members: 19
---

# test color settings regressions.py

**Cohesion:** 0.12 - loosely connected
**Members:** 19 nodes

## Members
- [[_color_check_timeout_ms_for_action()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/player.py
- [[legacy timeout은 per-action timeout이 모두 기본값일 때만 사용한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[legacy 단일 timeout만 설정한 기존 호출 경로도 기존 값으로 동작해야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_click_color_check_has_independent_timeout_defaults_per_action()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_color_check_mouse_down_wait_time_compensates_following_event_timestamps()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_color_settings_regressions.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_main_window_persists_color_settings_in_qsettings_contract()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_overlay_start_methods_force_visible_on_top_contract()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_plain_mouse_down_does_not_compensate_timestamps()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_player_does_not_use_legacy_for_only_one_non_default_action()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_player_selects_timeout_by_color_check_action()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[test_player_uses_legacy_click_color_timeout_when_action_timeouts_are_default()]] - code - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[대기무시중지 동작은 각자 독립 timeout 기본값을 가져야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[색 설정은 매크로 파일 저장 없이도 앱 설정으로 저장복원되어야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[색 체크 timeout 세분화지속성 회귀 테스트.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[색 체크 대기 시간이 끼어도 다음 이벤트들이 과거 target으로 몰려 급가속하지 않아야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[일반 녹화재생 오버레이도 hint처럼 위치 재설정+showraiseupdate 경로를 타야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[일반 클릭에는 인위적인 timestamp 보정을 넣지 않는다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py
- [[클릭 색 체크 runtime은 이벤트의 mismatch action별 timeout을 선택해야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_color_settings_regressions.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_color_settings_regressions.py
SORT file.name ASC
```

## Connections to other communities
- 25 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 4 edges to [[_COMMUNITY_execute event PlayState test]]

## Top bridge nodes
- [[_color_check_timeout_ms_for_action()]] - degree 6, connects to 2 communities
- [[test_color_check_mouse_down_wait_time_compensates_following_event_timestamps()]] - degree 4, connects to 2 communities
- [[test_plain_mouse_down_does_not_compensate_timestamps()]] - degree 4, connects to 2 communities
- [[test_player_does_not_use_legacy_for_only_one_non_default_action()]] - degree 4, connects to 1 community
- [[test_player_selects_timeout_by_color_check_action()]] - degree 4, connects to 1 community