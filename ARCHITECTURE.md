# ARCHITECTURE.md — 모듈 구조 및 의존성 규칙

> 에이전트가 새 기능을 추가할 때 반드시 이 파일을 먼저 읽어야 합니다.
> 의존성 방향을 어기는 코드는 작성하지 않습니다.

---

## 1. 3-Layer 구조

```
┌─────────────────────────────────────┐
│           UI Layer                  │  PyQt6. 사용자와 직접 상호작용.
│  main_window / sequencer / editor   │  Core를 호출하고 결과를 표시.
└────────────────┬────────────────────┘
                 │ 호출 (단방향)
┌────────────────▼────────────────────┐
│           Core Layer                │  비즈니스 로직. PyQt6 임포트 금지.
│  recorder / player / macro_file     │  pytest headless 테스트 가능해야 함.
│  script_engine                      │
└────────────────┬────────────────────┘
                 │ 호출 (단방향)
┌────────────────▼────────────────────┐
│         Platform Layer              │  Win32 API ctypes 래퍼.
│  win32/hooks / sendinput / dpi      │  OS 종속 코드는 여기에만 존재.
└─────────────────────────────────────┘
```

**의존성 방향: UI → Core → Platform (역방향 절대 금지)**

- UI가 Platform을 직접 임포트하는 것 금지
- Core가 UI를 임포트하는 것 금지
- Platform이 Core/UI를 임포트하는 것 금지

---

## 2. 모듈별 책임

### Platform Layer — win32/

#### hooks.py
- Win32 `SetWindowsHookEx(WH_MOUSE_LL)` / `WH_KEYBOARD_LL` 등록/해제
- 단일 메시지 펌프 스레드에서 콜백 처리
- 콜백에서는 `perf_counter_ns()` 타임스탬프 찍고 deque에 push만 함
- `get_pixel_color(x, y) → tuple[int,int,int]` : GetPixel 래퍼
- `find_window(title_contains) → HWND | None` : EnumWindows 래퍼
- 외부 공개 인터페이스:
  ```python
  def start_hook(queue: deque) -> None
  def stop_hook() -> None
  def get_pixel_color(x: int, y: int) -> tuple[int, int, int]
  def find_window(title_contains: str) -> int | None
  ```

#### sendinput.py
- Win32 `SendInput()` 래퍼
- 마우스 이동, 클릭, 드래그, 키 입력을 원자적으로 전송
- 외부 공개 인터페이스:
  ```python
  def send_mouse_move(x: int, y: int) -> None
  def send_mouse_click(x: int, y: int, button: str) -> None
  def send_mouse_drag(x1: int, y1: int, x2: int, y2: int) -> None
  def send_key(vk_code: int, is_down: bool) -> None
  ```

#### dpi.py
- 논리 해상도 조회 (`GetSystemMetrics` + DPI 보정)
- 비율 좌표 → 실제 픽셀 변환
- 외부 공개 인터페이스:
  ```python
  def get_logical_screen_size() -> tuple[int, int]
  def ratio_to_pixel(x_ratio: float, y_ratio: float) -> tuple[int, int]
  def pixel_to_ratio(x: int, y: int) -> tuple[float, float]
  ```

---

### Core Layer

#### recorder.py
- hooks.py의 deque를 소비하는 소비자 스레드
- raw 이벤트를 MacroEvent 객체로 변환
- 이벤트 id 생성 (`secrets.token_hex(4)`)
- 좌표를 dpi.py 통해 비율로 정규화
- 판별 금지: 클릭/드래그/노이즈 분류는 하지 않음
- 외부 공개 인터페이스:
  ```python
  def start_recording() -> None
  def stop_recording() -> MacroData   # raw_events 포함 전체 구조 반환
  ```

#### player.py
- MacroData의 events 배열을 순서대로 재생
- 절대 타임스탬프 기준 재생 (드리프트 보정 포함)
- 재생 시 click/drag 판별 (settings 임계값 사용)
- color_trigger: hooks.get_pixel_color() 폴링
- window_trigger: hooks.find_window() 폴링
- sendinput.py 호출로 실제 입력 전송
- 외부 공개 인터페이스:
  ```python
  def play(macro: MacroData, speed: float = 1.0,
           on_event: Callable | None = None,
           on_complete: Callable | None = None,
           on_error: Callable | None = None) -> None
  def stop() -> None
  def pause() -> None
  def resume() -> None
  ```

#### macro_file.py
- JSON 직렬화 / 역직렬화
- 스키마 버전 마이그레이션
- 저장 시 .bak 자동 생성
- events 편집 기능 (raw_events 보존 원칙):
  ```python
  def delete_mouse_moves(macro: MacroData) -> MacroData
  def set_delay_all(macro: MacroData, delay_ms: int) -> MacroData
  def set_delay_single(macro: MacroData, event_id: str, delay_ms: int) -> MacroData
  def reset_to_raw(macro: MacroData) -> MacroData
  ```
- 외부 공개 인터페이스:
  ```python
  def load(path: str) -> MacroData
  def save(macro: MacroData, path: str) -> None
  ```

#### script_engine.py
- condition / loop 이벤트 처리
- DSL expression 평가 (샌드박스 내에서만)
- 허용 함수: pixel_color(), wait(), random()
- 금지: eval() 외부 사용, 파일시스템 접근, 네트워크 접근

---

### UI Layer

#### main_window.py
- 메인 윈도우: 녹화 버튼, 재생 버튼, 파일 목록
- 상태 표시: 녹화 중 / 재생 중 / 대기
- Core 모듈과 Qt Signal/Slot으로 통신

#### sequencer.py
- 여러 매크로 JSON을 드래그앤드롭으로 순서 지정
- 실행 큐: MacroSequence 타입
- 각 매크로 상태 배지: 대기 / 실행중 / 완료 / 오류

#### editor.py
- 이벤트 목록 테이블 뷰 (id, type, timestamp, delay_override_ms)
- mouse_move 일괄 삭제 버튼
- 딜레이 개별/일괄 수정
- 원본으로 되돌리기 버튼
- color_trigger 삽입 UI: 좌표 클릭 → 색 자동 감지 → tolerance 설정

---

## 3. 핵심 데이터 타입

```python
# macroflow/types.py 에 정의

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class MacroEvent:
    id: str
    type: str
    timestamp_ns: int
    delay_override_ms: int | None = None
    # 타입별 추가 필드는 subclass로 정의

@dataclass
class MacroMeta:
    version: str
    app_version: str
    created_at: str
    screen_width: int
    screen_height: int
    dpi_scale: float
    author: str = ""
    description: str = ""

@dataclass
class MacroSettings:
    click_dist_threshold_px: int = 8
    click_time_threshold_ms: int = 300
    default_playback_speed: float = 1.0
    color_trigger_check_interval_ms: int = 50
    color_trigger_default_timeout_ms: int = 10000

@dataclass
class MacroData:
    meta: MacroMeta
    settings: MacroSettings
    raw_events: list[MacroEvent]   # 절대 수정 안 함
    events: list[MacroEvent]       # 재생/편집 대상
    is_edited: bool = False
```

---

## 4. 스레드 모델

```
Main Thread (Qt Event Loop)
  └─ UI 이벤트 처리, Signal/Slot

Recording Thread (daemon)
  └─ Win32 메시지 펌프 (WH_MOUSE_LL + WH_KEYBOARD_LL)
  └─ 콜백 → deque에 push (최소 처리)

Consumer Thread (daemon)
  └─ deque에서 pop → MacroEvent 변환 → recorder 버퍼에 적재

Playback Thread (daemon)
  └─ events 순서대로 타이밍 계산 → sendinput 호출
  └─ color_trigger / window_trigger 폴링
  └─ 완료/오류 시 Qt Signal로 Main Thread에 통보
```

**스레드 간 통신 규칙:**
- Recording/Consumer ↔ Core: `collections.deque` (lock-free)
- Core ↔ UI: Qt Signal/Slot만 사용 (직접 Qt 객체 참조 금지)
- 재생 중단: `threading.Event` 플래그 사용

---

## 5. 에러 처리 원칙

- color_trigger timeout → on_timeout 설정에 따라 처리
  - "error": PlaybackError 발생 → UI에 에러 다이얼로그
  - "skip": 다음 이벤트로 진행 (경고 로그)
  - "retry": 처음 이벤트부터 재시도 (최대 3회)
- 재생 중 예외 → Playback Thread가 catch → Qt Signal로 UI에 전달
- Core 모듈은 예외를 삼키지 않음. 항상 위로 전파

---

## 6. 테스트 전략

| 레이어 | 테스트 방법 |
|---|---|
| Platform (win32/) | 실제 Windows 환경에서만 테스트 가능. CI는 skip |
| Core | pytest headless. win32/ 모듈은 Mock으로 대체 |
| UI | pytest-qt. Core는 Mock으로 대체 |

```python
# tests/conftest.py
@pytest.fixture
def mock_win32(monkeypatch):
    monkeypatch.setattr("macroflow.win32.hooks.get_pixel_color",
                        lambda x, y: (255, 255, 255))
    monkeypatch.setattr("macroflow.win32.sendinput.send_mouse_click",
                        lambda *a, **kw: None)
```
