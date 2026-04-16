# 코드 스타일 리뷰

## 리뷰 개요
- **대상 언어**: Python 3.11+
- **적용 스타일 가이드**: PEP 8, Google Python Style
- **파일 수**: 13
- **총 발견 수**: 🔴 8 / 🟡 18 / 🟢 9

---

## 발견 사항

### 🔴 필수 수정

1. **[main_window.py:545]** — 라인 길이 초과 (E501)
   - 현재: `def _on_error(exc: Exception, _ev: threading.Event = done_event, _eh: list[str] = error_holder) -> None:`
   - 제안:
     ```python
     def _on_error(
         exc: Exception,
         _ev: threading.Event = done_event,
         _eh: list[str] = error_holder,
     ) -> None:
     ```
   - 이유: ruff 기본 88자 초과. 가독성 저하.

2. **[main_window.py:536, 560, 572]** — 프라이빗 속성 직접 접근 (`player._stop_flag`)
   - 현재: `if player._stop_flag.is_set():  # type: ignore[attr-defined]`
   - 제안: `player.py`에 `is_stop_requested() -> bool` 공개 함수 추가 후 사용
   - 이유: `_stop_flag`는 모듈 내부 상태. 외부에서 직접 접근하면 캡슐화 위반. `# type: ignore` 어노테이션이 타입 시스템 우회를 명시하고 있어 구조적 문제를 시사.

3. **[hooks.py:185, 197]** — Win32 콜백 파라미터명 camelCase (ruff N803)
   - 현재: `def _mouse_proc(nCode: int, wParam: int, lParam: int) -> int:`
   - 제안: 각 함수 끝에 `# noqa: N803` 추가, 또는 파일 상단에 `# ruff: noqa: N803` 추가하고 Win32 콜백 시그니처임을 주석으로 명시
   - 이유: ruff는 camelCase 파라미터를 N803으로 오류 처리. Win32 API 콜백 규칙상 불가피하나 억제 표기가 필요.

4. **[hooks.py:405-422]** — `find_window()` 내부에서 매 호출마다 `_WNDENUMPROC` 타입 재생성
   - 현재:
     ```python
     def find_window(title_contains: str) -> int | None:
         _WNDENUMPROC = ctypes.WINFUNCTYPE(...)  # 호출마다 재생성
     ```
   - 제안: `_WNDENUMPROC`를 모듈 상단 상수로 추출
   - 이유: 함수 호출마다 ctypes 함수 타입 객체를 재생성하는 낭비. 상수는 모듈 레벨에 위치해야 함(UPPER_SNAKE_CASE 규칙).

5. **[script_engine.py:270-275]** — `_color_matches` public-내부 함수에 Docstring 없음
   - 현재: `def _color_matches(...) -> bool:` — docstring 없음
   - 제안: `player.py`의 동일 함수처럼 Google style docstring 추가
   - 이유: `player.py`의 `_color_matches`에는 docstring이 있으나 `script_engine.py`의 동일 함수에는 없어 일관성 위반. 두 함수는 중복 코드이기도 함.

6. **[main.py:58]** — 함수 내부 상수가 UPPER_SNAKE_CASE이나 모듈 레벨 아님
   - 현재: `MB_ICONERROR = 0x10` (함수 `_fatal_dialog` 내부)
   - 제안: 모듈 레벨로 이동 `_MB_ICONERROR: int = 0x10`
   - 이유: 상수는 UPPER_SNAKE_CASE이며 모듈 레벨에 위치해야 함. 함수 내부 상수는 매 호출마다 재바인딩됨.

7. **[recorder.py:326]** — 잘못된 DPI 스케일 추정 + TODO 없이 방치
   - 현재: `dpi_scale=_screen_w / 1920.0,  # 단순 추정; dpi.get_dpi_scale()로 대체 가능`
   - 제안: `dpi_scale=get_dpi_scale()` (이미 임포트 가능한 함수 사용)
   - 이유: `win32.dpi.get_dpi_scale()`이 이미 존재하는데 수작업 추정값을 사용 중. 주석 자체가 "대체 가능"하다고 인정하면서 수정하지 않음. 기능 결함이자 스타일 위반(알려진 결함을 TODO 없이 방치).

8. **[sequencer.py:183-184]** — 인스턴스 메서드 직접 패치 (`method-assign`)
   - 현재:
     ```python
     self._list.dragEnterEvent = self._drag_enter  # type: ignore[method-assign]
     self._list.dropEvent = self._drop_event       # type: ignore[method-assign]
     ```
   - 제안: `QListWidget`을 서브클래싱하여 `dragEnterEvent`/`dropEvent` 오버라이드
   - 이유: 인스턴스 메서드 직접 패치는 Python 안티패턴. `type: ignore` 어노테이션이 타입 시스템 우회를 명시. PyQt6에서는 서브클래싱이 권장 방법.

---

### 🟡 권장 수정

1. **[recorder.py:371]** — `get_event_count()`에서 락 없이 공유 변수 접근
   - 현재: `return len(_event_buffer)` — `_event_buffer_lock` 없음
   - 제안: `with _event_buffer_lock: return len(_event_buffer)` 또는 폴링 목적임을 주석으로 명시
   - 이유: `_event_buffer`는 consumer 스레드가 쓰는 공유 변수. GIL이 보호하나 명시적 락이 없으면 의도가 불분명.

2. **[player.py:195-198]** — `_wait_for_window`에서 "retry" 케이스 미처리
   - 현재: `elif event.on_timeout == "skip": logger.warning(...)` 이후 암묵적 통과
   - 제안: `else: raise PlaybackError(msg)` 또는 `match` 구문으로 명시적 처리
   - 이유: `on_timeout`이 "retry"인 경우 `_wait_for_window`는 아무 동작 없이 통과함. `_wait_for_color`에서는 명시적으로 처리하는데 불일치.

3. **[macro_file.py:412]** — 함수 내부 변수가 UPPER_SNAKE_CASE
   - 현재: `_GAP_NS = max(0, gap_ms) * 1_000_000`
   - 제안: `gap_ns = max(0, gap_ms) * 1_000_000`
   - 이유: `_GAP_NS`는 함수 내부 계산값이지 모듈 상수가 아님. UPPER_SNAKE_CASE는 모듈 레벨 상수에만 사용.

4. **[script_engine.py:79]** — `CounterNode._value` 런타임 상태가 dataclass 필드로 혼재
   - 현재: `_value: int = dataclasses.field(default=0, init=False, repr=False, compare=False)`
   - 제안: 런타임 상태를 `FlowEngine` 내부 딕셔너리(`counter_values: dict[str, int]`)로 분리
   - 이유: `dataclasses.asdict()`가 `_value`를 포함하므로 `_node_to_dict`에서 수동으로 `d.pop("_value", None)` 처리 필요. 설계 복잡성 증가.

5. **[player.py:149-154]** — `_execute_event` 내부 lazy import
   - 현재: `from macroflow.script_engine import execute_condition`
   - 제안: 파일 상단에서 임포트 (순환 의존성이 없다면)
   - 이유: 지연 임포트는 순환 의존성 우회가 아닌 경우 권장되지 않음.

6. **[main_window.py:279-310]** — 이모지/특수문자 혼재 사용
   - 현재: `● 녹화`, `▶ 재생`(특수문자) vs `📂 열기`, `💾 저장`(이모지)
   - 제안: 전체적으로 이모지 또는 특수문자 한 가지 방식으로 통일
   - 이유: 일관성 결여. 폰트 환경에 따라 렌더링 차이 발생 가능.

7. **[script_engine.py:544]** — `# noqa: S307`에 이유 미기재
   - 현재: `result = bool(eval(event.expression, sandbox_globals))  # noqa: S307`
   - 제안: `# noqa: S307  # 의도적 eval — sandbox_globals로 builtins 차단, 허용 함수만 노출`
   - 이유: 보안 관련 억제 주석에는 반드시 이유를 기재해야 함.

8. **[favorites.py:110]** — `add_favorite`의 `macro_data: object` 타입 힌트 부정확
   - 현재: `def add_favorite(self, macro_data: object, name: str) -> bool:`
   - 제안: `def add_favorite(self, macro_data: MacroData, name: str) -> bool:`
   - 이유: 함수 내부에서 `MacroData`로 처리하며 `type: ignore[arg-type]`가 필요해짐. 정확한 타입 힌트 사용 필요.

9. **[hooks.py:24], [sendinput.py:17], [dpi.py:15]** — 모듈 레벨 `assert` 사용
   - 현재: `assert sys.platform == "win32", "..."`
   - 제안: `if sys.platform != "win32": raise ImportError("...")`
   - 이유: `python -O` 최적화 모드에서 `assert`는 비활성화됨. `ImportError`가 의도에 더 적합.

10. **[editor.py:110]** — `_build_rows` 함수에 Args/Returns 섹션 누락
    - 현재: 한 줄 설명만 있음
    - 제안: Google style Args/Returns 추가
    - 이유: 130줄 이상의 복잡한 함수임에도 파라미터 설명 없음.

11. **[sequencer.py:256-268]** — `_sync_items_from_list` 파일명 텍스트 기반 역매핑
    - 현재: `if item.path.name in text` — 같은 이름의 파일이 있으면 오작동
    - 제안: `QListWidgetItem`의 `UserRole`에 Path 저장 후 정확한 매핑 사용
    - 이유: 같은 파일명이 다른 경로에 존재할 때 오작동 가능. 잠재적 버그.

12. **[main_window.py]** — `_on_play_complete`, `_on_play_error`, `_stop_playback` 코드 중복
    - 현재: 세 함수 모두 동일한 5줄 상태 리셋 코드 반복
    - 제안: `_reset_playback_state()` 헬퍼 메서드 추출
    - 이유: DRY 원칙 위반. 추후 변경 시 3곳 모두 수정 필요.

13. **[script_engine.py:100]** — `EndNode.status` 필드에 `Literal` 타입 미사용
    - 현재: `status: str = "success"    # "success" | "error"`
    - 제안: `status: Literal["success", "error"] = "success"`
    - 이유: `types.py`에서 `Literal`을 적극 활용하는데 `script_engine.py`에서는 미사용. 일관성 부족.

14. **[script_engine.py:88]** — `WaitFixedNode.next` 필드명이 Python 내장 함수 섀도잉 (ruff A003)
    - 현재: `next: str | None = None`
    - 제안: `next_node_id: str | None = None`
    - 이유: `next`는 Python 내장 함수. ruff A003(builtin shadowing)으로 검출됨.

15. **[favorites.py:278]** — `_sanitize_filename` 함수에 docstring 없음
    - 현재: docstring 없음
    - 제안: Google style docstring 추가 (보안 관련 로직이므로 더욱 중요)
    - 이유: 파일명 새니타이징은 보안과 직결된 함수임에도 문서화 없음.

16. **[player.py:397-401]** — `get_progress()` 분자/분모가 모두 모듈 레벨 변수이나 thread-safety 주석 없음
    - 현재: `return _current_event_idx / _total_events` — 스레드 안전 여부 불명확
    - 제안: 주석으로 GIL 보호 가정을 명시 또는 `threading.Lock()` 추가
    - 이유: UI 폴링 타이머가 메인 스레드에서 읽고, 재생 스레드가 값을 씀.

17. **[recorder.py:223-239]** — `_consumer_loop`에서 `len(_raw_queue) > 0` 보다 `bool(_raw_queue)` 사용 권장
    - 현재: `if _raw_queue and len(_raw_queue) > 0:`
    - 제안: `if _raw_queue:`
    - 이유: `deque`의 `bool()` 변환은 비어있으면 False이므로 `len() > 0` 중복 체크 불필요.

18. **[main_window.py 전체]** — 상태 문자열 "idle", "recording", "stopping", "playing"이 리터럴로 사용
    - 현재: `if self._state == "idle":`, `self._state = "playing"` 등 문자열 직접 비교
    - 제안: `Literal["idle", "recording", "stopping", "playing"]` 또는 `enum.StrEnum` 사용
    - 이유: 오타 시 런타임에서만 발견됨. `Enum`이나 `Literal` 타입으로 컴파일 타임 검증 가능.

---

### 🟢 참고 사항

1. **[types.py 전체]** — 모든 dataclass에 완전한 Google style docstring과 타입 힌트 100% 적용. 프로젝트 내 가장 모범적인 파일.

2. **[dpi.py 전체]** — 간결하고 완성도 높음. 모든 public 함수에 Args/Returns 완비.

3. **[macro_file.py]** — Python 3.10+ `match/case` 구문을 적극 활용하여 분기 로직의 가독성이 우수.

4. **[recorder.py:43-104]** — Win32 상수를 섹션 구분 주석과 함께 명확하게 그룹화.

5. **[player.py:251-253]** — `last_significant_event_end_ns` 변수명이 의도를 충분히 표현하는 좋은 네이밍 예.

6. **[hooks.py:88-95]** — LRESULT/HOOKPROC 타입 정의에 64비트 호환성 이유를 인라인 주석으로 명시. Win32 취약점 방지 지식이 코드에 내재화됨.

7. **[script_engine.py:532-541]** — eval 샌드박스 globals에서 `__builtins__: {}` 명시, 허용 함수만 노출하는 구조가 명확하고 의도가 읽힘.

8. **[favorites.py 전체]** — 위젯 코드임에도 신호 docstring, 오류 처리, 타입 힌트가 일관됨.

9. **[전체 파일]** — `from __future__ import annotations` 일관 적용, 섹션 구분 주석(`# ── ... ──`) 통일, `core-beliefs.md` 원칙 번호 인라인 참조 등 팀 내 코딩 컨벤션 준수도가 높음.

---

## 반복 패턴

| 패턴 | 발생 횟수 | 자동 수정 가능 | 권장 규칙 |
|---|---|---|---|
| `# type: ignore[attr-defined]`로 내부 속성 접근 | 3회 (main_window.py) | 아니오 | 공개 API 추가 후 제거 |
| 함수 내부 lazy import | 8회+ (player.py, sequencer.py, favorites.py 등) | 부분적 | 순환 의존이 아니면 상단으로 이동 |
| `assert` 대신 `ImportError` 미사용 | 3회 (win32 모듈 3개) | 예 | win32 모듈 공통 헬퍼로 추출 |
| 상태 문자열 리터럴 직접 비교 | 다수 (main_window.py) | 아니오 | `Literal` 또는 `StrEnum` 도입 |
| 중복 상태 리셋 코드 블록 | 3회 (main_window.py) | 아니오 | `_reset_playback_state()` 헬퍼 추출 |

---

## 칭찬할 점

1. **일관된 모듈 구조**: 모든 파일이 `from __future__ import annotations`를 첫 줄에 배치하고 `# ── 섹션명 ──` 구분 주석을 일관되게 사용. 파일 전체 가독성 매우 높음.

2. **설계 원칙 코드 내 참조**: `player.py`, `recorder.py`, `hooks.py` 등에서 `core-beliefs.md 원칙 N`을 docstring/주석에 직접 참조하여 코드와 설계 문서의 연결성이 탁월.

3. **타입 힌트 완성도**: Python 3.10+ 스타일(`X | Y`, `list[X]`, `tuple[X, Y]`, `Literal`)의 현대적 타입 힌트를 전 파일에서 일관 적용.

4. **Win32 ctypes 품질**: `argtypes`/`restype` 완전 선언, 64비트 LRESULT 처리 주석, `LLKHF_INJECTED` 플래그로 주입 이벤트 필터링 등 Win32 API 코드가 매우 방어적이고 정확함.

5. **threading 안전성 의식**: `_event_buffer_lock`, Qt Signal 기반 스레드 간 통신, `daemon=True` 일관 사용 등 경쟁 조건을 최소화하려는 노력이 코드 전반에 보임.
