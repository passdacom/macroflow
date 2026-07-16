---
type: community
cohesion: 0.03
members: 66
---

# mock.py hooks.py get logical

**Cohesion:** 0.03 - loosely connected
**Members:** 66 nodes

## Members
- [[FindWindow Mock — 항상 None 반환.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[GetCursorPos Mock — 설정된 커서 위치 반환.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[GetPixel Mock — 설정된 색 반환.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[GetSystemMetrics Mock — 기본 1920×1080.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[Hook 등록 Mock — 아무것도 하지 않음.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[Hook을 등록하고 메시지 펌프 스레드를 시작한다.      Args         queue 캡처된 원시 이벤트를 쌓을 deque.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[WH_KEYBOARD_LL (긴급 중지 전용) 메시지 펌프.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[WH_MOUSE_LL + WH_KEYBOARD_LL을 단일 스레드에서 처리하는 메시지 펌프.      WM_QUIT 수신 시 Hook 해제 후]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[WM_QUIT을 펌프 스레드에 보내 Hook을 해제하고 스레드를 종료한다.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[Win32 API 레이어.  Windows에서는 실제 ctypes 구현을 사용. Linux개발 환경(openclaw 등)에서는 Mock을 자동]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/__init__.py
- [[Win32 DPI 스케일링 처리.  논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다. 모듈 임포트 시 SetProcessDpiAware]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[Win32 Low-Level Hook — WH_MOUSE_LL  WH_KEYBOARD_LL.  단일 메시지 펌프 스레드에서 마우스·키보드 이벤]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[Win32 Mock 구현 — Linux개발 환경용.  openclaw 같은 Linux 서버에서 Claude Code가 작업할 때 자동으로 사용]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[_KBDLLHOOKSTRUCT]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[_MSLLHOOKSTRUCT]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[_POINT]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[__getattr__()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/__init__.py
- [[__init__.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/__init__.py
- [[__init__.py_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/__init__.py
- [[__init__.py_2]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/__init__.py
- [[_emg_keyboard_proc()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[_emg_pump()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[_keyboard_proc()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[_message_pump()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[_mouse_proc()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[dpi.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[find_window()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[get_cursor_pos()_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[get_cursor_pos()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[get_dpi_scale()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[get_logical_screen_size()_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[get_logical_screen_size()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[get_pixel_color()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[hooks.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[mock.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[pixel_to_ratio()_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[pixel_to_ratio()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[ratio_to_pixel()_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[ratio_to_pixel()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_key()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_mouse_button()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_mouse_click()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_mouse_drag()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_mouse_move()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_mouse_wheel()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[send_text()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[set_mock_pixel_color()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[start_emergency_hook()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[start_hook()_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[start_hook()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[start_recording()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/recorder.py
- [[stop_emergency_hook()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[stop_hook()_1]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[stop_hook()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[기본 모니터의 논리 해상도를 반환한다 (DPI 스케일링 보정 후).      Returns         (width, height) 픽셀 단]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[긴급 중지 Hook Mock — 아무것도 하지 않음.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[긴급 중지 전용 키보드 LL Hook 콜백.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[마우스 LL Hook 콜백 — 최소 처리 후 즉시 반환.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[마우스 Low-Level Hook 이벤트 구조체.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[시스템 DPI 배율을 반환한다 (96dpi 기준 1.0).      Returns         DPI 배율. 예 125% DPI → 1.2]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[키보드 LL Hook 콜백 — 최소 처리 후 즉시 반환.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[키보드 Low-Level Hook 이벤트 구조체.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[테스트에서 GetPixel 반환값을 제어하기 위한 헬퍼.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/mock.py
- [[픽셀 절대 좌표를 화면 크기 대비 비율로 변환한다.      core-beliefs.md 원칙 4 — 녹화 시 비율로 저장, 재생 시 현재 해상]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py
- [[현재 마우스 커서의 화면 좌표(픽셀)를 반환한다.      Returns         (x, y) 픽셀 좌표 튜플.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/hooks.py
- [[화면 비율 좌표를 현재 해상도의 픽셀 좌표로 변환한다.      Args         x_ratio X 좌표 비율 (0.0~1.0).]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/win32/dpi.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/mock.py_hooks.py_get_logical
SORT file.name ASC
```

## Connections to other communities
- 13 edges to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 7 edges to [[_COMMUNITY_execute event PlayState test]]
- 3 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 3 edges to [[_COMMUNITY_convert raw TestConvertRaw stop]]
- 1 edge to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 1 edge to [[_COMMUNITY_rdp runtime safety smoke.py]]

## Top bridge nodes
- [[start_recording()]] - degree 5, connects to 3 communities
- [[hooks.py]] - degree 17, connects to 2 communities
- [[get_logical_screen_size()_1]] - degree 7, connects to 2 communities
- [[pixel_to_ratio()_1]] - degree 6, connects to 2 communities
- [[ratio_to_pixel()_1]] - degree 6, connects to 2 communities