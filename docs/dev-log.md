# MacroFlow 개발 로그

> **규칙**: 이 파일은 **append-only**다. 기존 항목을 절대 삭제하거나 수정하지 않는다.
> 새 개발 내용은 최상단(최신 순)에 추가한다.
> Claude Code 에이전트와 개발자 모두 이 규칙을 준수한다.

---

## v0.2.3 — 2026-04-14

### 즐겨찾기 탭 추가

#### 구현 범위 (파일 3개)
| 파일 | 변경 내용 |
|---|---|
| `ui/favorites.py` | `FavoritesWidget` 신규 — 즐겨찾기 목록, 우클릭 메뉴, open_in_editor/add_to_sequencer 신호 |
| `ui/main_window.py` | 즐겨찾기 탭 추가, "⭐ 즐겨찾기에 추가" 툴바 버튼, `_save_and_add_to_favorites()` |

#### UX 설계 포인트
- **저장 위치**: `favorites/` 폴더 (macros/ 폴더와 별도)
- **이름 지정**: 저장 시 `QInputDialog`로 파일명 입력 (공백·특수문자 자동 정리)
- **중복 이름**: 자동으로 `_2`, `_3` 접미사 추가
- **더블클릭**: 매크로 에디터로 즉시 로드 + 에디터 탭 전환
- **우클릭**: 시퀀서에 추가 / 즐겨찾기에서 제거
- **F6/F7**: 즐겨찾기 탭에서는 녹화(F6) 비활성화, 재생(F7)은 정상 동작

---

### 키 입력 수정 버그 수정 (`ui/editor.py`)

#### 원인
`_NAME_TO_VK` 딕셔너리에 `.`, `,`, `;` 등 OEM 특수문자 키가 없어서
새 키 이름 입력 시 VK 코드가 원래 키(fallback_vk)로 유지됨.
예: 키 이름을 "1" → "."으로 변경해도 vk_code=0x31(1)이 그대로 남아 재생 시 "1"이 입력됨.

#### 수정
- `_NAME_TO_VK`에 OEM 키 추가: `.`(0xBE), `,`(0xBC), `;`(0xBA), `/`(0xBF), `` ` ``(0xC0), `[`(0xDB), `]`(0xDD), `'`(0xDE), `-`(0xBD), `=`(0xBB), `\`(0xDC)
- 숫자패드 키 추가: `num0`~`num9`, `num*`, `num+`, `num-`, `num.`, `num/`
- F13~F24 키 추가 (기존 F12까지만 있었음)
- 수식어 키 확장: `lshift`, `rshift`, `lctrl`, `rctrl`, `lalt`, `ralt`, `lwin`, `rwin`
- `_key_name_to_vk()` 개선: 딕셔너리 미스 시 Win32 `VkKeyScanA` API로 단일 문자 자동 변환 (Windows 환경에서만)

---

### 이전 매크로 복원 기능 (`ui/main_window.py`)

#### 기능 설명
F6 실수 입력으로 잘 녹화된 매크로가 새 녹화로 덮어써지는 상황을 대비.

#### 동작 흐름
1. 매크로가 에디터에 로드된 상태에서 F6(새 녹화 시작) 누름
2. 기존 매크로를 `_prev_macro`에 메모리 백업 + `pre_recording_YYYYMMDD_HHMMSS.json`으로 파일 백업
3. 새 녹화 완료 후 툴바에 **"↩ 이전 매크로 복원"** 버튼 활성화
4. 버튼 클릭 → 확인 다이얼로그 → 이전 매크로를 에디터에 복원
5. 복원 후 버튼 비활성화, 다음 녹화 시작 시 새로 백업

#### 설계 원칙
- **비간섭**: 정상적인 새 녹화 시에도 자동 백업만 하고 다이얼로그 없이 진행
- **1클릭 복원**: 실수 감지 후 버튼 클릭 한 번으로 복원
- **파일 안전망**: 앱 크래시에도 `pre_recording_*.json`에서 복구 가능

---

## v0.2.2 — 2026-04-01

### 마우스 휠 녹화·재생 지원 (수직/수평 모두)

#### 구현 범위 (파일 10개)
| 파일 | 변경 내용 |
|---|---|
| `types.py` | `MouseWheelEvent` 추가 (delta, axis, x_ratio, y_ratio) |
| `recorder.py` | `WM_MOUSEWHEEL(0x020A)` / `WM_MOUSEHWHEEL(0x020E)` 처리, mouseData 상위 16비트에서 부호 있는 delta 추출 |
| `sendinput.py` | `send_mouse_wheel(x, y, delta, horizontal)` 추가 — `MOUSEEVENTF_WHEEL` / `MOUSEEVENTF_HWHEEL` |
| `mock.py` | `send_mouse_wheel` Mock 추가 |
| `win32/__init__.py` | `send_mouse_wheel` 익스포트 |
| `macro_file.py` | `mouse_wheel` 직렬화/역직렬화, `edit_wheel_delta()` 유틸 |
| `player.py` | `MouseWheelEvent` 재생: 기록된 위치로 커서 선이동 후 휠 전송 |
| `editor.py` | 연속 같은 축 휠 이벤트 그룹핑, 청록색, 편집 다이얼로그 (방향·노치 수 조정, 그룹→단일 병합) |
| `tests/test_recorder.py` | 수직 상/하, 수평, 멀티노치 테스트 4개 추가 |
| `tests/test_macro_file.py` | wheel roundtrip, edit_wheel_delta 테스트 2개 추가 |

#### UX 설계 포인트
- **그룹핑**: 연속된 같은 축 휠 이벤트 → 에디터에서 1행으로 압축 표시 (`↑ 휠 위 ×3  Δ+360  @ (45.2%, 30.1%)`)
- **편집 다이얼로그**: 방향 라디오 버튼 + 노치 수 SpinBox + 실시간 Δ 미리보기
- **편집 결과**: 그룹 전체를 primary 이벤트 1개로 병합 (Undo 지원)
- **재생**: `send_mouse_move` → `send_mouse_wheel` 순서 보장 (타겟 윈도우 정확도)
- **테스트**: 48/48 통과

---

## v0.2.1 — 2026-04-01

### UI/UX 개선 6종 (`main_window.py`, `sequencer.py`, `editor.py`)

#### ① 시퀀서 자동 저장 (다이얼로그 제거)
- **변경 전**: "💾+ 시퀀서" 버튼 → 파일 저장 다이얼로그 → 시퀀서 추가
- **변경 후**: 다이얼로그 없이 `macros/macro_YYYYMMDD_HHMMSS.json`으로 즉시 저장
- `_get_macros_dir()`: exe 위치(frozen) 또는 cwd(dev) 하위 `macros/` 폴더 자동 생성

#### ② 시퀀서 더블클릭 → 에디터 로드
- `MacroSequencerWidget.open_in_editor = pyqtSignal(str)` 신호 추가
- 리스트 아이템 더블클릭 → `open_in_editor` 발생 → 에디터 탭으로 자동 전환 + 파일 로드

#### ③ 탭 기반 F6/F7 동작 분리
- **에디터 탭**: F6=녹화 토글, F7=재생 토글 (기존 동일)
- **시퀀서 탭**: F6 비활성화, F7=시퀀서 실행/중지 토글
- `_on_tab_changed()`: 탭 전환 시 툴바 상태 자동 갱신
- `_update_toolbar()`: 시퀀서 탭에서 녹화 버튼 비활성화, 재생 버튼 텍스트 변경

#### ④ 파일 다이얼로그 초기 폴더
- `_get_default_dir()`: `sys.frozen` 감지 → exe 부모 디렉토리 / 개발 환경 → cwd
- 기존 `Path.home()` 참조를 전부 `_get_default_dir()`로 교체 (main_window, sequencer 양쪽)

#### ⑤ SpinBox 너비 확대 (숫자 잘림 해소)
- repeat: 72→90px, interval: 80→95px, range start/end: 60→75px
- 화살표 버튼에 숫자가 가려지던 문제 해결

#### ⑥ 마우스 위치 3초 카운트다운 캡처 (`editor.py`)
- 위치 편집 다이얼로그에 **"📍 화면에서 직접 지정 (3초 후 캡처)"** 버튼 추가
- 버튼 클릭 → 다이얼로그 최소화 → 1초 간격 카운트다운 (3→2→1) → `GetCursorPos()` 호출
- `pixel_to_ratio()` 변환 후 x/y SpinBox에 자동 입력 → 다이얼로그 복원

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
