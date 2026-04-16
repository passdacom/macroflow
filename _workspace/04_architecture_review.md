# 아키텍처 리뷰

## 리뷰 개요
- **아키텍처 건강 수준**: 🟡 개선 필요
- **아키텍처 패턴**: 레이어드 아키텍처 (UI → 도메인 → Win32) + 절차적 모듈 패턴(player, recorder)
- **총 발견 수**: 🔴 3 / 🟡 6 / 🟢 4

---

## 구조적 발견 사항

### 🔴 구조적 문제

#### 1. **player.py** — 모듈 레벨 전역 상태 (Thread-Safety / 단일 인스턴스 강제)
- **문제**: `_playback_thread`, `_stop_flag`, `_pause_flag`, `_current_event_idx`, `_total_events`가 모듈 레벨 전역 변수로 선언되어 있다. 두 개의 `play()` 호출이 동시에 발생하면 이전 스레드가 아직 실행 중일 때 `_stop_flag`·`_playback_thread`가 덮어써진다. 특히 `get_progress()`에서 `_current_event_idx / _total_events`를 읽는 동안 다른 스레드에서 `_total_events=0`으로 초기화되면 ZeroDivisionError가 발생할 수 있다.
- **영향**: 시퀀서가 FlowEngine을 통해 `player.play()`를 반복 호출할 때 경쟁 조건 발생 가능. 단위 테스트에서 병렬 테스트 케이스가 전역 상태를 공유해 테스트 격리 불가.
- **리팩토링 제안**: `PlaybackController` 클래스로 캡슐화. `_stop_flag`, `_pause_flag`를 인스턴스 필드로 이동. 공개 인터페이스(`play`, `stop`, `pause`, `resume`, `is_playing`, `get_progress`)를 메서드로 유지.

```python
class PlaybackController:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._current_idx: int = 0
        self._total: int = 0
    def play(self, macro, speed=1.0, ...) -> None: ...
    def stop(self) -> None: ...
```

#### 2. **main_window.py** — God Class (SRP 위반, 과도한 책임 집중)
- **문제**: `MainWindow`가 다음 책임을 동시에 갖고 있다:
  1. 상태 머신 관리 (idle/recording/stopping/playing)
  2. Win32 RegisterHotKey / nativeEvent 처리
  3. 파일 I/O (열기/저장/임시저장/즐겨찾기 저장)
  4. 반복 재생 워커 스레드 직접 생성 및 관리 (`_repeat_worker` 클로저)
  5. player 모듈의 `_stop_flag` private 접근 (`player._stop_flag.is_set()`)
  6. emergency hook 시작/중지 직접 호출
  7. 최근 녹화 메뉴 관리
  현재 약 1,086줄, 메서드 40개 이상.
- **영향**: 기능 추가 시 이 파일만 커지는 구조. 개별 책임 단위 테스트 불가. Win32 직접 접근이 UI 계층에 산재.
- **리팩토링 제안**:
  - `RecordingController` — 녹화 시작/중지 로직 분리
  - `PlaybackManager` — 반복 재생 스레드 관리 분리 (현재 `_repeat_worker` 클로저 포함)
  - `HotkeyManager` — RegisterHotKey / nativeEvent 처리 분리
  - `FileManager` — 파일 열기/저장/임시저장 분리

#### 3. **main_window.py** — player 모듈 private 접근 (캡슐화 위반)
- **문제**: `_repeat_worker` 내부에서 `player._stop_flag.is_set()`을 직접 참조한다 (라인 536, 560, 572). 이는 `player` 모듈의 내부 구현에 UI가 강결합됨을 의미한다.
- **영향**: `player.py`가 `PlaybackController` 클래스로 리팩토링될 때 UI 코드도 함께 수정해야 하는 의존성 사슬 형성.
- **리팩토링 제안**: `player.is_stopping() -> bool` 공개 함수 추가. 또는 PlaybackController 클래스로 전환 시 자연스럽게 해결.

---

### 🟡 설계 개선

#### 1. **recorder.py** — 모듈 레벨 전역 상태 (player.py와 동일 패턴)
- **문제**: `_recording`, `_raw_queue`, `_consumer_thread`, `_event_buffer`, `_event_buffer_lock` 등 모든 상태가 모듈 레벨. `player.py`와 동일한 단일 인스턴스 강제 문제.
- **영향**: 테스트 격리 어려움. 다만 실제 앱에서는 녹화가 항상 단일 인스턴스여야 하므로 실용적 영향은 낮음.
- **리팩토링 제안**: `RecordingSession` 클래스로 캡슐화하되, 우선순위는 player.py보다 낮음.

#### 2. **script_engine.py** — 혼합 책임 (FlowEngine + 인라인 이벤트 실행)
- **문제**: `script_engine.py`가 두 가지 서로 다른 레이어의 책임을 가진다:
  1. `.macroflow` 플로우차트 파일 실행 (`FlowEngine`, `MacroFlow`, 노드 타입들)
  2. 인라인 `ConditionEvent`/`LoopEvent` 평가 (`execute_condition`, `execute_loop`)
  플로우 노드 데이터클래스(`MacroNode`, `ColorCheckNode` 등)와 직렬화/역직렬화도 동일 파일에 존재.
- **영향**: FlowEngine이 직접 `from macroflow import player`로 player를 임포트해 순환 위험은 없지만, player.py가 `from macroflow.script_engine import execute_condition`을 임포트하는 역방향 의존이 런타임에 발생함(지연 임포트).
- **리팩토링 제안**: `flow_engine.py`(FlowEngine + 노드 타입), `inline_executor.py`(execute_condition, execute_loop)로 분리.

#### 3. **player.py / script_engine.py** — `_hex_to_rgb`, `_color_matches` 중복
- **문제**: `player.py`와 `script_engine.py` 양쪽에 동일한 `_hex_to_rgb`, `_color_matches` 함수가 복제되어 있다.
- **영향**: 버그 수정 시 두 곳 모두 수정 필요. DRY 원칙 위반.
- **리팩토링 제안**: `macroflow/utils/color.py`로 추출하거나 `types.py`에 유틸리티로 포함.

#### 4. **macro_file.py** — 편집 유틸리티 함수의 위치
- **문제**: `macro_file.py`가 파일 I/O(`load`, `save`)와 편집 변환(`delete_mouse_moves`, `set_delay_all`, `set_delay_single`, `reset_to_raw`, `edit_key_value`, `edit_wheel_delta`, `merge_macros`, `edit_position`)을 함께 포함한다. 편집 함수들은 I/O와 무관한 순수 변환 함수다.
- **영향**: 파일 접근 없이 순수 변환만 할 때도 파일 I/O 관련 의존성이 따라옴. 응집도 약화.
- **리팩토링 제안**: `macro_file.py`는 `load`/`save`만 유지하고, 순수 변환 함수는 `macro_editor.py` 또는 `macro_ops.py`로 분리.

#### 5. **win32 레이어 — RegisterHotKey 직접 호출 누수**
- **문제**: `main_window.py`의 `_register_hotkeys()` 및 `_unregister_hotkeys()`에서 `ctypes.windll.user32.RegisterHotKey` / `UnregisterHotKey`를 UI 레이어에서 직접 호출한다. 이는 Win32 API가 `win32/` 래퍼를 우회해 누출된 사례다.
- **영향**: 핫키 등록 로직이 UI와 결합. win32 레이어의 분리 원칙 부분 위반.
- **리팩토링 제안**: `win32/hotkey.py` 추가, `register_global_hotkey(hwnd, id, vk)` / `unregister_global_hotkey(hwnd, id)` 함수 제공.

#### 6. **CounterNode._value** — 런타임 상태를 데이터클래스 필드에 저장
- **문제**: `CounterNode`의 `_value` 필드는 런타임 실행 상태지만 `dataclass` 필드로 선언되어 있다. `dataclasses.asdict()` 호출 후 `_value` 키를 수동으로 `pop()`하는 불안정한 패턴이 사용됨.
- **영향**: `asdict()` 동작 변경 시(예: 중첩 처리) `_value`가 직렬화에 포함될 수 있음.
- **리팩토링 제안**: `_value`를 `__post_init__`에서 초기화하는 별도 속성으로 분리하거나, `CounterNode`를 `@dataclass` 대신 일반 클래스로 정의.

---

### 🟢 참고 사항

#### 1. **player.py** — 드리프트 보정 로직
- 절대 타임스탬프 기반 재생과 `play_start_ns` 전진 보정 방식은 색/창 트리거의 실제 실행 시간을 흡수해 이후 이벤트 순서를 올바르게 유지하는 견고한 설계. 구현 복잡도에 비해 타이밍 정확도가 높다.

#### 2. **win32/ 레이어** — 타입 선언의 정확성
- `LRESULT = ctypes.c_ssize_t`, `_HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ...)` 등 64비트 호환 타입을 정확히 선언. 잘못된 c_long 사용 시 Hook 반환값 상위 비트 쓰레기로 이벤트 차단 문제를 주석으로 명시. 플랫폼 하드웨어 인터페이스로서 완성도가 높다.

#### 3. **script_engine.py** — eval() 샌드박스 설계
- `__builtins__: {}` 완전 차단 + 허용 함수만 노출하는 샌드박스 구조. `random` 모듈 전체가 아닌 `random()` 함수 하나만 노출하는 세밀한 설계. 보안 원칙 준수.

#### 4. **macro_file.py** — 불변 데이터 반환 패턴
- 편집 유틸리티 함수가 원본 `MacroData`를 수정하지 않고 항상 새 인스턴스를 반환하는 함수형 패턴을 일관되게 사용. `raw_events`를 절대 수정하지 않는 원칙도 코드에 반영됨.

---

## SOLID 원칙 평가

| 원칙 | 상태 | 주요 위반 | 비고 |
|---|---|---|---|
| **S** 단일 책임 | 🔴 위반 | `MainWindow` — 상태머신·파일IO·반복재생·핫키·오버레이 통합 | `script_engine.py`도 FlowEngine+인라인실행 혼재 |
| **O** 개방-폐쇄 | 🟡 부분 | `_execute_event()`의 `isinstance` 분기 체인 | 새 이벤트 타입 추가 시 player.py, macro_file.py, editor.py 모두 수정 필요 |
| **L** 리스코프 치환 | 🟢 준수 | `MacroEvent` 서브클래스들이 기반 클래스 계약 위반 없음 | dataclass 상속 구조 올바름 |
| **I** 인터페이스 분리 | 🟡 부분 | `player.py`의 공개 함수가 불완전해 UI가 `_stop_flag`를 직접 참조 | 모듈 함수 API에 `is_stopping()` 누락 |
| **D** 의존성 역전 | 🟡 부분 | UI가 player/recorder 구체 모듈에 직접 의존 | 추상 인터페이스 없음; 팀 내 소규모 앱에서 실용적 수준 |

---

## 의존성 그래프

```
main.py
  └─→ ui/main_window.py
        ├─→ macroflow.types
        ├─→ macroflow.recorder
        ├─→ macroflow.player  ← player._stop_flag 직접 접근 ⚠
        ├─→ macroflow.macro_file
        ├─→ macroflow.win32 (get_cursor_pos, get_pixel_color, emergency hook)
        ├─→ ctypes 직접 (RegisterHotKey)  ← win32 레이어 우회 ⚠
        ├─→ ui/editor.py
        ├─→ ui/sequencer.py
        ├─→ ui/favorites.py
        └─→ ui/overlay.py

macroflow.player
  ├─→ macroflow.types
  ├─→ macroflow.win32 (send_*, ratio_to_pixel, get_pixel_color, find_window)
  └─→ macroflow.script_engine (지연 임포트 — execute_condition, execute_loop)

macroflow.recorder
  ├─→ macroflow.types
  └─→ macroflow.win32 (start_hook, stop_hook, get_logical_screen_size, pixel_to_ratio)

macroflow.script_engine (FlowEngine)
  ├─→ macroflow.types
  ├─→ macroflow.macro_file (지연 임포트)
  ├─→ macroflow.player (지연 임포트)
  └─→ macroflow.win32 (지연 임포트 — get_pixel_color, ratio_to_pixel)

macroflow.macro_file
  └─→ macroflow.types

macroflow.win32/
  ├─→ hooks.py (ctypes only)
  ├─→ sendinput.py → dpi.py
  └─→ dpi.py (ctypes only)
```

**순환 참조**: 없음 (지연 임포트로 회피 성공)
**문제적 방향**: `main_window.py → player._stop_flag` (private 접근), `main_window.py → ctypes 직접` (RegisterHotKey)

---

## 레이어 분석

| 레이어 | 모듈 | 관심사 | 의존 방향 | 상태 |
|---|---|---|---|---|
| **진입점** | `main.py` | 앱 부트스트랩, 로깅 설정 | → UI | 🟢 깔끔 |
| **UI** | `ui/main_window.py` | 상태머신, 핫키, 파일IO, 반복재생 | → 도메인, Win32 직접 | 🔴 God Class |
| **UI** | `ui/editor.py` | 이벤트 테이블 표시·편집 | → 도메인 | 🟡 적절 (대형) |
| **UI** | `ui/sequencer.py` | 시퀀스 실행 UI | → 도메인 | 🟢 적절 |
| **UI** | `ui/favorites.py` | 즐겨찾기 목록 | → (파일 경로만) | 🟢 적절 |
| **도메인** | `player.py` | 재생 엔진 | → Win32, types, script_engine | 🟡 전역 상태 |
| **도메인** | `recorder.py` | 녹화 엔진 | → Win32, types | 🟡 전역 상태 |
| **도메인** | `macro_file.py` | 직렬화 + 순수 변환 | → types | 🟡 혼합 책임 |
| **도메인** | `script_engine.py` | FlowEngine + 인라인 실행 | → types, player(지연), win32(지연) | 🟡 혼합 책임 |
| **데이터** | `types.py` | 이벤트·메타 dataclass | 없음 | 🟢 이상적 |
| **인프라** | `win32/hooks.py` | WH_LL Hook, GetPixel | ctypes만 | 🟢 격리 잘됨 |
| **인프라** | `win32/sendinput.py` | SendInput | ctypes, dpi | 🟢 격리 잘됨 |
| **인프라** | `win32/dpi.py` | DPI 스케일 | ctypes만 | 🟢 격리 잘됨 |

---

## 테스트 가능성 평가

| 모듈 | DI 지원 | 모킹 용이 | 부수효과 격리 | 점수 |
|---|---|---|---|---|
| `types.py` | N/A | N/A | 완전 순수 | ⭐⭐⭐⭐⭐ |
| `macro_file.py` | 없음 | load/save만 mocking 필요 | 파일 I/O만 | ⭐⭐⭐⭐ |
| `player.py` | ❌ 전역 상태 | win32 모킹 필요, 전역 리셋 필요 | 스레드·전역변수 | ⭐⭐ |
| `recorder.py` | ❌ 전역 상태 | win32.start_hook 모킹 필요 | 스레드·전역변수 | ⭐⭐ |
| `script_engine.py` | 부분 (FlowEngine 콜백) | win32 모킹 필요 | eval 샌드박스 격리 | ⭐⭐⭐ |
| `ui/main_window.py` | ❌ | PyQt6 환경 필수, 너무 많은 의존 | GUI·스레드·파일·Win32 | ⭐ |
| `ui/editor.py` | 부분 | PyQt6 환경 필수 | GUI 부수효과 | ⭐⭐⭐ |
| `win32/hooks.py` | ❌ | ctypes.windll 모킹 어려움 | Win32 API 직접 | ⭐⭐ |
| `win32/sendinput.py` | ❌ | ctypes.windll 모킹 어려움 | Win32 API 직접 | ⭐⭐ |

**가장 테스트하기 쉬운 영역**: `types.py`, `macro_file.py` 편집 유틸리티 함수들 (순수 함수, 파일 의존 없음)
**가장 어려운 영역**: `ui/main_window.py` — 단위 테스트 사실상 불가, 통합 테스트 필요

---

## 설계 패턴 분석

| 패턴 | 적용 여부 | 적절성 | 비고 |
|---|---|---|---|
| 레이어드 아키텍처 | 적용됨 | 🟢 적절 | UI→도메인→Win32 방향 대체로 준수 |
| 상태 머신 | 적용됨 (문자열 기반) | 🟡 개선 가능 | `_state: str` — enum 또는 State 클래스 명시화 권장 |
| 옵저버 (Qt Signal/Slot) | 적용됨 | 🟢 적절 | 스레드 경계 신호 전달에 올바른 사용 |
| 절차적 모듈 (player, recorder) | 적용됨 | 🟡 제한적 | 단일 인스턴스 보장되나 테스트 격리 불가 |
| 팩토리 (dict_to_event) | 적용됨 | 🟢 적절 | match-case 기반 명확한 분기 |
| 불변 데이터 반환 (copy.deepcopy) | 적용됨 | 🟢 적절 | macro_file 편집 함수들이 새 MacroData 반환 |
| 전략 패턴 (콜백 DI) | 부분 적용 | 🟢 적절 | player.play()의 on_event/on_complete/on_error |
| Singleton | 암묵적 적용 | 🟡 개선 가능 | 모듈 레벨 전역 상태가 사실상 싱글턴 역할 |

---

## 칭찬할 점

1. **types.py의 완전한 독립성**: Win32나 PyQt6 의존성이 전혀 없어 어떤 환경에서도 임포트 가능. 데이터 모델과 플랫폼 코드의 분리가 명확하다.

2. **win32 레이어의 책임 격리**: `hooks.py`, `sendinput.py`, `dpi.py`가 Win32 API 호출을 완전히 캡슐화하고 있으며, 상위 레이어가 ctypes를 직접 다루지 않아도 된다 (`RegisterHotKey` 예외 제외).

3. **불변 데이터 패턴 (macro_file.py)**: 편집 유틸리티 함수가 원본 `MacroData`를 수정하지 않고 항상 새 인스턴스를 반환하는 함수형 패턴을 일관되게 사용. `raw_events`를 절대 수정하지 않는 원칙도 코드에 반영됨.

4. **절대 타임스탬프 기반 재생 + 드리프트 보정 (player.py)**: `play_start_ns` 전진 보정으로 색/창 트리거 실제 대기 시간을 흡수하는 설계가 탁월하다. `last_significant_event_end_ns` 클램프로 음수 딜레이 역전 방지도 세밀하게 처리됨.

5. **Qt Signal/Slot 스레드 경계 처리**: 워커 스레드에서 직접 UI를 건드리지 않고 `pyqtSignal`을 통해 메인 스레드로 안전하게 전달하는 구조가 일관되게 지켜진다. `_sig_recording_done`, `_sig_play_complete` 등이 모범 사례.
