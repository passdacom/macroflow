# MacroFlow 개발 로그

> **규칙**: 이 파일은 **append-only**다. 기존 항목을 절대 삭제하거나 수정하지 않는다.
> 새 개발 내용은 최상단(최신 순)에 추가한다.
> Claude Code 에이전트와 개발자 모두 이 규칙을 준수한다.

---

## v0.2.0 — 2026-04-01

### 빌드 버전 관리 개선
- **문제**: EXE 파일명이 항상 `MacroFlow.exe`로 동일 → 버전 구분 불가
- **해결**: `build.yml`이 `pyproject.toml`에서 버전을 자동 읽어 파일명에 반영
  - EXE 파일명: `MacroFlow-v{version}-build{run_number}.exe`
  - 릴리즈 태그: `v{version}-build{run_number}`
  - 릴리즈명: `MacroFlow v{version} Build {run_number}`
- **규칙**: 기능 추가/수정 시 `pyproject.toml`과 `src/macroflow/__init__.py`의 `__version__`을 함께 올린다

### 자동저장 관리 (`main_window.py`)
- 녹화 완료 시 `%APPDATA%/MacroFlow/temp/recording_YYYYMMDD_HHMMSS.json` 자동 저장
- **최근 10개만 유지**: 11번째 이상은 오래된 순으로 자동 삭제
- **파일 메뉴 → "최근 녹화"** 서브메뉴: 임시 저장 파일 목록 표시, 클릭 시 바로 로드

### 영구 저장 + 시퀀서 연동 (`main_window.py`, `sequencer.py`)
- 툴바에 **"💾+ 시퀀서"** 버튼 추가
- 동작: 파일 저장 다이얼로그 → 영구 저장 → 시퀀서 탭에 자동 추가 → 시퀀서 탭으로 자동 전환
- `sequencer.add_macro_file(path)` 공개 메서드 추가

### 재생 위치 추적 (`player.py`, `editor.py`, `main_window.py`)
- 재생 중 현재 실행 이벤트의 테이블 행이 **자동 선택 + 화면 중앙으로 스크롤**
- `player.on_event` 콜백 시그니처 변경: `(event) → (idx, event)` (원본 인덱스 포함)
- `_sig_play_event(int)` 신호로 worker thread → UI thread 안전 전달
- `editor.highlight_event()` 스크롤 힌트를 `PositionAtCenter`로 변경

### 구간 재생 (`main_window.py`, `editor.py`, `player.py`)
- 툴바에 **구간: [시작] ~ [끝]** SpinBox 추가 (0=전체)
- 사용 예: 시작=50, 끝=70 → display row 50~70만 재생
- `editor.get_event_range_for_rows(start_row, end_row)` → `(event_start, event_end_exclusive)` 변환
- `player.play(event_range=(start, end))` 파라미터 추가
- 구간 첫 이벤트의 timestamp를 기준점으로 재조정 → 구간 시작 시 즉시 재생

---

## v0.1.x — 2026-03-31 ~ 2026-04-01

### 재생 중 ESC×3 긴급 중지 (`win32/hooks.py`, `main_window.py`)
- **문제**: 재생 중에는 LL Hook이 없어 ESC×3이 window 포커스 있을 때만 동작
- **해결**: 재생 시작 시 전용 `WH_KEYBOARD_LL` Hook (`EmergencyHookPump`) 설치
  - `LLKHF_INJECTED` 플래그 체크 → SendInput 주입 ESC(매크로 자체) 오인식 방지
  - 재생 완료/중지/오류 시 Hook 자동 해제
- `start_emergency_hook(callback)` / `stop_emergency_hook()` 공개 함수 추가

### 색상 체크(Color Trigger) 녹화 중 삽입 (`win32/hooks.py`, `recorder.py`, `main_window.py`)
- **동작**: 녹화 중 F7 누르면 현재 마우스 커서 위치의 픽셀 색상을 캡처하여 `ColorTriggerEvent` 삽입
- 재생 시 해당 좌표의 픽셀이 기록된 색(허용 오차 ±10)이 될 때까지 최대 10초 대기, 타임아웃 시 skip
- `GetCursorPos` Win32 API 추가 (`get_cursor_pos()`)
- `recorder.inject_color_trigger(x_ratio, y_ratio, color_hex)` 공개 함수 추가
- 상태바에 삽입된 색상과 좌표 표시

### 마우스/키보드 녹화 중 멈춤 버그 수정 (`win32/hooks.py`)
- **근본 원인**: `_HOOKPROC` 반환 타입이 `ctypes.c_long`(32비트)이었으나 x64 Windows에서 LRESULT는 64비트(`LONG_PTR`)
  - 상위 32비트가 쓰레기 값 → Windows가 non-zero로 해석 → "이벤트 차단" → 마우스/키보드 완전 정지
- **수정**: `LRESULT = ctypes.c_ssize_t`(포인터 크기)로 변경, 모든 Win32 함수에 argtypes/restype 명시
- `GetModuleHandleW(None)` hMod 전달로 일부 Windows 버전 SetWindowsHookExW 실패 방지

### 녹화 중 ESC×3 긴급 중지 (`recorder.py`, `main_window.py`)
- `recorder._consumer_loop()`에서 ESC key_down 3회(0.5초 이내) 감지 → Qt Signal 발사
- window 포커스 없이도 동작 (LL Hook consumer thread에서 직접 감지)

### 긴급 중지 후 재생 불가 버그 수정 (`player.py`)
- **원인**: `player.stop()` 후 `_stop_flag`가 set 상태로 남아있어 다음 재생 시 즉시 종료
- **수정**: `stop()` 마지막에 `_stop_flag.clear()` 추가

### 이벤트 에디터 UX 개선 (`editor.py`)
- **그룹 표시**: mouse_down+up → "클릭(왼쪽/오른쪽)" 1행 / key_down+up → "키 입력" 1행
  - 이동이 3개 초과인 경우 "드래그"로 자동 분류
- **새 컬럼**: `[#, 타입, 내용, 시간(ms), 딜레이(ms)]`
- **Undo/Redo**: Ctrl+Z / Ctrl+Y, 최대 50단계 (`_undo_stack: deque`)
- **더블클릭 편집**: 내용 셀 → 키값/위치 변경 다이얼로그, 딜레이 셀 → 딜레이 설정
- **Delete 키**: 선택 행 삭제
- **마우스 이동 토글**: 이동 이벤트 표시/숨김 (비파괴)
- **컨텍스트 메뉴**: 딜레이·키값·위치·삭제
- `highlight_event(idx)`: 재생 중 현재 이벤트 행 하이라이트

### 인라인 재생 설정 (`main_window.py`)
- 재생 버튼 클릭 시 팝업 다이얼로그 제거 → 즉시 재생
- 툴바에 속도(0.5x/1.0x/2.0x/5.0x), 반복 횟수, 반복 간격 컨트롤 인라인 배치

### macro_file.py 편집 유틸 추가
- `edit_key_value(macro, event_id, new_key, new_vk_code)` → KeyEvent 키 변경
- `edit_position(macro, event_id, new_x_ratio, new_y_ratio)` → 마우스 이벤트 위치 변경

---

## v0.1.0 초기 구현 — 2026-03-31 이전

### 아키텍처
- 3-레이어: UI → Core → Platform (역방향 의존 금지)
- Win32 API 직접 호출 (pynput 사용 금지)
- 녹화 시 클릭/드래그 판별 금지 → RAW 저장 → 재생 시 임계값 판별

### 구현 완료 파일 목록
| 파일 | 내용 |
|---|---|
| `types.py` | 모든 이벤트 타입 (MouseButtonEvent, MouseMoveEvent, KeyEvent, WaitEvent, ColorTriggerEvent, WindowTriggerEvent, ConditionEvent, LoopEvent), MacroData, MacroMeta, MacroSettings |
| `main.py` | 진입점, 파일 로그, ctypes 오류 다이얼로그 |
| `macro_file.py` | JSON 저장/로드, 편집 유틸 (delete_moves, set_delay, reset_to_raw) |
| `player.py` | 절대 타임스탬프 기준 재생, 드리프트 보정, click/drag 판별 |
| `recorder.py` | LL Hook 기반 녹화, VK 코드 변환, F6/F7 필터링 |
| `script_engine.py` | FlowEngine(.macroflow), execute_condition/loop, DSL 샌드박스 |
| `win32/hooks.py` | WH_MOUSE_LL, WH_KEYBOARD_LL, GetPixel, GetCursorPos, 긴급 중지 Hook |
| `win32/sendinput.py` | SendInput 래퍼 (mouse_move, mouse_button, mouse_drag, key) |
| `win32/dpi.py` | DPI 보정, 좌표 비율 변환, GetSystemMetrics |
| `win32/mock.py` | 비-Windows 환경 Mock (CI/개발용) |
| `ui/main_window.py` | 메인 창, 상태머신, F6/F7 RegisterHotKey, 툴바, 자동저장 |
| `ui/editor.py` | 이벤트 에디터 (그룹 표시, Undo/Redo, 더블클릭 편집, 구간 매핑) |
| `ui/overlay.py` | 녹화/재생 미니 오버레이 |
| `ui/sequencer.py` | 드래그앤드롭 시퀀서, FlowEngine 연동, .macroflow 저장/로드 |

### 이벤트 포맷 (hooks.py → recorder.py)
```
("m", timestamp_ns, wParam, (x_px, y_px, mouse_data))  # 마우스
("k", timestamp_ns, wParam, (vk_code, scan_code, flags))  # 키보드
```

### CI/CD
- GitHub Actions: `lint-test`(ubuntu) → `build-exe`(windows) → `release`(ubuntu)
- PyInstaller onefile, console=False, UPX 비활성화, DPI Aware 매니페스트

### 핵심 설계 원칙 (core-beliefs.md)
1. 녹화는 무손실 RAW 저장
2. 이벤트 순서는 OS가 보장 (단일 메시지 펌프)
3. 절대 타임스탬프 기준 재생 (time.sleep 루프 금지)
4. 좌표를 화면 비율로 정규화 (DPI 독립)
5. SendInput 직접 호출
6. MacroData 편집은 항상 새 인스턴스 반환 (불변 패턴)
7. GetPixel로 단일 픽셀만 읽기 (스크린샷 API 금지)
8. 스레드 → UI 통신은 Qt Signal/Slot만

---

## 알려진 미해결 사항 / 향후 과제

- [ ] 창 제목 감지(WindowTriggerEvent) UI 편집 지원
- [ ] 색상 트리거 허용 오차(tolerance)·타임아웃 UI 편집 지원
- [ ] 재생 중 이벤트 인덱스 오버레이에도 표시
- [ ] macroflow DSL 스크립트 에디터 (script_engine.py 연동)
