# Graph Report - /root/.openclaw/workspace/macroflow  (2026-05-29)

## Corpus Check
- Large corpus: 783 files · ~254,195 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 1074 nodes · 4077 edges · 24 communities detected
- Extraction: 38% EXTRACTED · 62% INFERRED · 0% AMBIGUOUS · INFERRED: 2512 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MouseMoveEvent|MacroData MouseButtonEvent KeyEvent MouseMoveEvent]]
- [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions|MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- [[_COMMUNITY_EventEditorWidget add single row|EventEditorWidget add single row]]
- [[_COMMUNITY_MacroSequencerWidget FlowEngine EndNode MacroFlow|MacroSequencerWidget FlowEngine EndNode MacroFlow]]
- [[_COMMUNITY_FavoritesWidget refresh tree save|FavoritesWidget refresh tree save]]
- [[_COMMUNITY_execute event PlayState player.py|execute event PlayState player.py]]
- [[_COMMUNITY_convert raw TestConvertRaw hooks.py|convert raw TestConvertRaw hooks.py]]
- [[_COMMUNITY_build rows DisplayRow editor|build rows DisplayRow editor]]
- [[_COMMUNITY_test editor table.py table|test editor table.py table]]
- [[_COMMUNITY_load test macro file.py|load test macro file.py]]
- [[_COMMUNITY_mock.py find window get|mock.py find window get]]
- [[_COMMUNITY_test editor insertions.py insert|test editor insertions.py insert]]
- [[_COMMUNITY_test editor remark.py FakeTableForWidth|test editor remark.py FakeTableForWidth]]
- [[_COMMUNITY_test editor capture.py start|test editor capture.py start]]
- [[_COMMUNITY_append recording recording done|append recording recording done]]
- [[_COMMUNITY_key name test editor|key name test editor]]
- [[_COMMUNITY_test favorites search.py get|test favorites search.py get]]
- [[_COMMUNITY_summary text test editor|summary text test editor]]
- [[_COMMUNITY_conftest.py mock hook mock|conftest.py mock hook mock]]
- [[_COMMUNITY_test version.py test package|test version.py test package]]
- [[_COMMUNITY_test package imports.py test|test package imports.py test]]
- [[_COMMUNITY_Return whether complete repeat|Return whether complete repeat]]
- [[_COMMUNITY_Return user facing repeat|Return user facing repeat]]
- [[_COMMUNITY_init .py|init .py]]

## God Nodes (most connected - your core abstractions)
1. `MacroData` - 214 edges
2. `MouseButtonEvent` - 196 edges
3. `KeyEvent` - 161 edges
4. `MouseMoveEvent` - 153 edges
5. `ColorTriggerEvent` - 149 edges
6. `TextInputEvent` - 146 edges
7. `MouseWheelEvent` - 136 edges
8. `MacroSettings` - 131 edges
9. `WaitEvent` - 105 edges
10. `ConditionEvent` - 104 edges

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

### Community 0 - "MacroData MouseButtonEvent KeyEvent MouseMoveEvent"
Cohesion: 0.07
Nodes (194): Pure event insertion helpers for the MacroFlow event editor.  This module intent, Return events with click or double-click MouseButtonEvents inserted., Return events with one configured ColorTriggerEvent inserted., Return the source event index after which an editor insertion should occur., Insert events after an index and shift following timestamps to preserve timing., Return events with one TextInputEvent inserted and later timestamps shifted., MacroFlow 이벤트 에디터 위젯.  그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력. Undo/Redo,, 지정 행 클릭 이벤트의 색 체크(color_check_enabled)를 토글한다.          recorded_color가 없는 이벤트에서는 (+186 more)

### Community 1 - "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
Cohesion: 0.03
Nodes (65): 긴급 중지 Hook을 해제하고 스레드를 종료한다., stop_emergency_hook(), MainWindow, MacroFlow 메인 창.  전체 상태 머신(idle / recording / stopping / playing)을 관리한다. F6/F7 글로, 매크로 로드 후 구간 SpinBox 범위를 갱신한다., 파일 다이얼로그 초기 폴더를 반환한다.          PyInstaller 패키징 상태이면 exe 파일이 있는 폴더,         개발 환경, 경로에서 매크로를 로드하여 에디터에 표시한다., 시퀀서 더블클릭 시: 매크로를 로드하고 에디터 탭으로 전환한다. (+57 more)

### Community 2 - "EventEditorWidget add single row"
Cohesion: 0.05
Nodes (37): create_capture_controls(), create_delay_spin(), create_percentage_spin(), Small widget factories shared by MacroFlow editor dialogs., Create a position percentage spin box with the editor's shared bounds., Create a millisecond delay spin box with the editor's shared suffix., Create the standard F6 capture label/button pair used in editor dialogs., EventEditorWidget (+29 more)

### Community 3 - "MacroSequencerWidget FlowEngine EndNode MacroFlow"
Cohesion: 0.06
Nodes (58): _color_matches(), ColorCheckNode, CounterNode, _dict_to_node(), EndNode, execute_condition(), FlowEngine, _hex_to_rgb() (+50 more)

### Community 4 - "FavoritesWidget refresh tree save"
Cohesion: 0.05
Nodes (43): FavoritesWidget, MacroFlow 즐겨찾기 위젯 (트리 구조).  즐겨찾기를 그룹별로 분류하고 아코디언 트리 뷰로 표시한다. 그룹과 항목 모두 드래그앤드롭으로, 즐겨찾기 트리 위젯.      favorites/ 디렉토리와 _index.json 파일을 함께 관리한다.     새로 추가된 항목은 기본 그룹(, 즐겨찾기 디렉토리를 설정하고 트리를 초기 로드한다., MacroData를 즐겨찾기 폴더에 저장하고 기본 그룹에 추가한다.          Args:             macro_data: 저장할, _index.json 을 읽어 self._index 에 적재한다., self._index 를 _index.json 에 저장한다., 기본 그룹이 없으면 인덱스 맨 앞에 생성한다. (+35 more)

### Community 5 - "execute event PlayState player.py"
Cohesion: 0.04
Nodes (54): get_dpi_scale(), get_logical_screen_size(), pixel_to_ratio(), ratio_to_pixel(), Win32 DPI 스케일링 처리.  논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다. 모듈 임포트 시 SetProcessDpiAware, 기본 모니터의 논리 해상도를 반환한다 (DPI 스케일링 보정 후).      Returns:         (width, height) 픽셀 단, 시스템 DPI 배율을 반환한다 (96dpi 기준 1.0).      Returns:         DPI 배율. 예: 125% DPI → 1.2, 픽셀 절대 좌표를 화면 크기 대비 비율로 변환한다.      core-beliefs.md 원칙 4 — 녹화 시 비율로 저장, 재생 시 현재 해상 (+46 more)

### Community 6 - "convert raw TestConvertRaw hooks.py"
Cohesion: 0.04
Nodes (45): Exception, _emg_keyboard_proc(), _emg_pump(), get_cursor_pos(), _KBDLLHOOKSTRUCT, _keyboard_proc(), _message_pump(), _mouse_proc() (+37 more)

### Community 7 - "build rows DisplayRow editor"
Cohesion: 0.09
Nodes (47): _apply_row_metadata(), _build_color_trigger_row(), _build_condition_row(), _build_key_down_row(), _build_key_up_row(), _build_loop_row(), _build_mouse_down_row(), _build_mouse_move_row() (+39 more)

### Community 8 - "test editor table.py table"
Cohesion: 0.07
Nodes (25): _cell(), _is_hex_color(), Qt table rendering helpers for the MacroFlow event editor.  This module intentio, QSS 색상 박스에 안전하게 사용할 수 있는 #RRGGBB 값인지 검사한다., 표시 row가 내용 열에 색상 swatch 위젯을 사용해야 하면 True를 반환한다., 표시 row 하나를 QTableWidgetItem 목록으로 렌더링한다., _should_use_color_detail_widget(), _table_row_items() (+17 more)

### Community 9 - "load test macro file.py"
Cohesion: 0.13
Nodes (32): delete_mouse_moves(), edit_key_value(), edit_position(), _event_to_dict(), load(), merge_macros(), _migrate(), reset_to_raw() (+24 more)

### Community 10 - "mock.py find window get"
Cohesion: 0.07
Nodes (15): find_window(), get_cursor_pos(), get_logical_screen_size(), get_pixel_color(), Win32 Mock 구현 — Linux/개발 환경용.  openclaw 같은 Linux 서버에서 Claude Code가 작업할 때 자동으로 사용, GetSystemMetrics Mock — 기본 1920×1080., Hook 등록 Mock — 아무것도 하지 않음., 테스트에서 GetPixel 반환값을 제어하기 위한 헬퍼. (+7 more)

### Community 11 - "test editor insertions.py insert"
Cohesion: 0.22
Nodes (15): _base_timestamp_ns(), _insert_and_shift_events(), _insert_click_events(), _insert_color_trigger_event(), _insert_text_input_event(), _selected_insert_after_event_idx(), _ids(), test_insert_click_events_creates_double_click_sequence_and_shifts_tail() (+7 more)

### Community 12 - "test editor remark.py FakeTableForWidth"
Cohesion: 0.24
Nodes (10): _FakeTableForWidth, _import_editor(), _install_fake_pyqt(), _make_macro(), _make_widget(), test_content_column_has_compact_auto_fit_policy(), test_content_column_width_fits_contents_but_keeps_reference_minimum(), test_edit_remark_updates_macro_event_and_marks_edited() (+2 more)

### Community 13 - "test editor capture.py start"
Cohesion: 0.24
Nodes (10): _FakeWidget, _import_editor(), _install_fake_pyqt(), _make_widget(), Event editor F6 capture lifecycle behavior with Qt mocked out., _Signal, test_cancel_f6_capture_only_emits_when_active(), test_consume_f6_capture_runs_once_and_emits_end() (+2 more)

### Community 14 - "append recording recording done"
Cohesion: 0.24
Nodes (11): append_recording(), Helpers for appending a fresh recording to an existing macro.  This module is in, Return copies of ``events`` shifted so the first event starts at a timestamp., Append a newly recorded macro to ``base_macro`` and return a new MacroData., shift_event_timestamps(), _key(), _macro(), _move() (+3 more)

### Community 15 - "key name test editor"
Cohesion: 0.22
Nodes (8): key_name_to_vk(), Key-name to Windows VK-code mapping for the MacroFlow event editor.  This module, 키 이름 문자열을 VK 코드로 변환한다.      1) NAME_TO_VK 딕셔너리에서 찾는다.     2) Windows 환경에서 단일 문자이, Editor key-name to VK-code mapping tests., 키 매핑 helper는 Qt 런타임 없이 독립 import 가능해야 한다., test_editor_keys_import_does_not_eagerly_import_pyqt_widgets(), test_key_name_to_vk_maps_standard_names_and_aliases(), test_key_name_to_vk_returns_fallback_for_unknown_name()

### Community 16 - "test favorites search.py get"
Cohesion: 0.32
Nodes (7): _get_favorites_source(), 즐겨찾기 검색 필터 존재 여부 테스트., favorites.py 소스 코드를 직접 읽어 반환한다., FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다., FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다., test_favorites_widget_has_apply_search_filter(), test_favorites_widget_has_search_box_in_setup_ui()

### Community 17 - "summary text test editor"
Cohesion: 0.29
Nodes (6): Pure summary text helpers for the MacroFlow event editor., Return the event editor footer summary text., _summary_text(), Event editor summary text helper regression tests., test_summary_text_appends_edited_tag_when_macro_is_edited(), test_summary_text_matches_current_refresh_format_without_edited_tag()

### Community 18 - "conftest.py mock hook mock"
Cohesion: 0.33
Nodes (5): mock_hook(), mock_win32(), pytest 공통 픽스처.  win32 모듈을 mock으로 교체하여 Linux 개발 환경에서도 테스트 가능하게 한다., win32 Platform Layer 전체를 Mock으로 대체한다.      Core 레이어 테스트 시 반드시 사용한다., start_hook / stop_hook을 mock으로 대체하고 직접 주입 가능한 큐를 반환한다.      테스트에서 이 큐에 raw 이벤트를

### Community 19 - "test version.py test package"
Cohesion: 0.4
Nodes (4): 메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다., QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다., test_package_version_matches_project_metadata(), test_qapplication_version_uses_package_version()

### Community 20 - "test package imports.py test"
Cohesion: 0.5
Nodes (3): UI package import boundaries., 순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다., test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()

### Community 21 - "Return whether complete repeat"
Cohesion: 1.0
Nodes (1): Return whether a complete repeat-session stop was requested.

### Community 22 - "Return user facing repeat"
Cohesion: 1.0
Nodes (1): Return user-facing repeat cycle label, e.g. '3/10회'.

### Community 23 - "init .py"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **133 isolated node(s):** `MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag`, `파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다.`, `Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args:         title: 다이얼로그 제목.`, `MacroFlow 핵심 데이터 타입 정의.  모든 이벤트 타입, MacroData 컨테이너, 메타·설정 클래스를 여기에 정의한다. 이 모듈은 W`, `모든 매크로 이벤트의 공통 기반 클래스.      Attributes:         id: 8자리 hex 문자열. 녹화 시 생성, 이후 변경` (+128 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Return whether complete repeat`** (1 nodes): `Return whether a complete repeat-session stop was requested.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Return user facing repeat`** (1 nodes): `Return user-facing repeat cycle label, e.g. '3/10회'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `init .py`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MacroData` connect `MacroData MouseButtonEvent KeyEvent MouseMoveEvent` to `MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions`, `EventEditorWidget add single row`, `MacroSequencerWidget FlowEngine EndNode MacroFlow`, `FavoritesWidget refresh tree save`, `execute event PlayState player.py`, `convert raw TestConvertRaw hooks.py`, `build rows DisplayRow editor`, `load test macro file.py`, `test editor remark.py FakeTableForWidth`, `append recording recording done`?**
  _High betweenness centrality (0.290) - this node is a cross-community bridge._
- **Why does `EventEditorWidget` connect `EventEditorWidget add single row` to `MacroData MouseButtonEvent KeyEvent MouseMoveEvent`, `MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions`, `FavoritesWidget refresh tree save`, `test editor table.py table`, `test editor remark.py FakeTableForWidth`, `test editor capture.py start`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Why does `MainWindow` connect `MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions` to `MacroData MouseButtonEvent KeyEvent MouseMoveEvent`, `EventEditorWidget add single row`, `MacroSequencerWidget FlowEngine EndNode MacroFlow`, `FavoritesWidget refresh tree save`, `execute event PlayState player.py`, `convert raw TestConvertRaw hooks.py`, `append recording recording done`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Are the 212 inferred relationships involving `MacroData` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MacroData` has 212 INFERRED edges - model-reasoned connections that need verification._
- **Are the 193 inferred relationships involving `MouseButtonEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MouseButtonEvent` has 193 INFERRED edges - model-reasoned connections that need verification._
- **Are the 158 inferred relationships involving `KeyEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`KeyEvent` has 158 INFERRED edges - model-reasoned connections that need verification._
- **Are the 150 inferred relationships involving `MouseMoveEvent` (e.g. with `PlaybackError` and `_PlayState`) actually correct?**
  _`MouseMoveEvent` has 150 INFERRED edges - model-reasoned connections that need verification._