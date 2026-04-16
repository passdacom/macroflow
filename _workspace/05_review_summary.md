# 종합 코드 리뷰 보고서 — MacroFlow v0.2.5

> **리뷰 대상**: MacroFlow v0.2.5  
> **리뷰 일자**: 2026-04-14  
> **종합 기준**: Style(🔴8/🟡18/🟢9) + Security(Critical1/High2/Medium4/Low5) + Performance(🔴3/🟡6/🟢3) + Architecture(🔴3/🟡6/🟢4)

---

## 최종 판정

- **결과**: 🟡 Request Changes
- **근거**: 🔴 심각 항목 9개 (보안 Critical 1 포함), 🟡 권장 수정 다수
- **총평**: MacroFlow v0.2.5는 Win32 LL Hook 래핑, 절대 타임스탬프 재생, 불변 데이터 패턴 등 핵심 설계가 견고하고 코딩 컨벤션 준수도가 높다. 그러나 `eval()` 샌드박스 탈출(RCE 가능), `player.py` 전역 상태 경쟁 조건, God Class(`main_window.py`) 세 가지는 머지 전 반드시 해결해야 한다. 보안 Critical은 팀 내 배포 환경에서 악성 `.json` 파일 하나로 임의 코드 실행이 가능하므로 최우선 처리가 필요하다.

---

## 통합 발견 사항 (우선순위순)

### 🔴 즉시 수정 (머지 차단)

아래 9개 항목은 4개 영역 리뷰에서 🔴로 판정되었거나, 여러 영역에서 교차 확인된 심각 사항이다.

---

**1. [script_engine.py:544] — eval() 샌드박스 탈출 → RCE 가능** `[보안 CRIT-01]`

- **문제**: `__builtins__: {}` 로 빌트인을 차단해도 Python 객체 그래프 순회(`pixel_color.__class__.__mro__[-1].__subclasses__()`)로 `os`, `subprocess`, `ctypes` 등에 접근 가능. 악성 `.json` 파일을 여는 즉시 임의 코드 실행.
- **수정 방향**: `ast.parse()` + 허용 AST 노드 화이트리스트로 expression 사전 검증. `ast.Attribute` 노드는 무조건 거부. `expression` 필드 길이 상한(예: 512자) 추가.

```python
ALLOWED_NODES = {
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp,
    ast.Compare, ast.Call, ast.Constant, ast.Name,
    ast.And, ast.Or, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
}
ALLOWED_FUNC_NAMES = {"pixel_color", "wait", "random"}

def _validate_expression(expr: str) -> None:
    if len(expr) > 512:
        raise ValueError("expression 길이 초과")
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise ValueError(f"허용되지 않은 AST 노드: {type(node).__name__}")
        if isinstance(node, ast.Attribute):
            raise ValueError("속성 접근 금지")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNC_NAMES:
                raise ValueError("허용되지 않은 함수 호출")
```

> 내부 배포 도구 특성을 감안해 즉시 수정 후 재심 전제로 🟡 Request Changes 유지. 미수정 시 단독 🔴 Reject 조건.

---

**2. [script_engine.py:401-426] — 절대 경로 Path Traversal 우회** `[보안 HIGH-01]`

- **문제**: `MacroNode.macro_path`가 절대 경로이면 검증 없이 그대로 사용. `C:\Windows\System32\evil.json` 또는 UNC 경로 `\\attacker\share\payload.json` 지정 가능.
- **수정 방향**: 절대 경로도 허용 루트 목록 내에 있는지 검증.

```python
macro_path = Path(node.macro_path).resolve()
if not macro_path.is_relative_to(self._base_dir.resolve()):
    raise FlowError(f"보안: 허용 디렉토리 외부 경로 차단 ({node.macro_path!r})")
```

---

**3. [main.py:36-42 / script_engine.py:544] — DEBUG 로그에 민감 정보 기록** `[보안 HIGH-02]`

- **문제**: 배포 빌드에서 로그 레벨이 `DEBUG`로 고정. `ConditionEvent` 오류 시 expression 전체(비밀번호 등 포함 가능)가 로그 파일에 기록. 로그 파일 ACL 미설정으로 동일 PC 타 사용자 접근 가능.
- **수정 방향**: `MACROFLOW_DEBUG` 환경변수 없으면 `INFO` 레벨 적용. expression 내용을 로그에서 제거. `os.chmod(log_file, 0o600)` 적용.

---

**4. [sendinput.py:184-188] — send_mouse_drag() 내 time.sleep 반복 → 타이밍 드리프트** `[성능 PERF-02 / core-beliefs 원칙 3 위반]`

- **문제**: 드래그 보간 루프에서 `time.sleep(0.01)` × 10회 = 100ms 강제 블로킹. player.py 절대 타임스탬프 보정 루프 바깥에서 발생하므로 이후 모든 이벤트가 ~100ms 이상 지연. `core-beliefs.md 원칙 3` 직접 위반.
- **수정 방향**: sleep 제거, 단일 `SendInput` 배치 호출로 대체. `drag_step_delay_ms=0` 옵션 파라미터 제공.

---

**5. [hooks.py:379-382] — get_pixel_color() 예외 시 GDI 핸들 누수** `[성능 PERF-03]`

- **문제**: `GetPixel` 예외 발생 시 `ReleaseDC` 미호출. 색 트리거 폴링 루프에서 반복 호출되므로 장시간 실행 시 GDI 핸들 고갈.
- **수정 방향**: `try/finally` 블록으로 `ReleaseDC` 보장. 트레이드오프 없음.

---

**6. [sendinput.py:110-113] — _normalize() 매 호출마다 syscall** `[성능 PERF-01]`

- **문제**: `get_logical_screen_size()`(Win32 API)를 마우스 이벤트마다 호출. 빠른 마우스 이동 구간(초당 수십 건)에서 타이밍 정밀도 저하.
- **수정 방향**: 모듈 초기화 시 1회 캐싱. 다중 모니터 전환 이벤트 구독 시 캐시 무효화.

---

**7. [player.py:전역] — 모듈 레벨 전역 상태 5개 → 경쟁 조건 + 테스트 불가** `[아키텍처 ARCH-01]`

- **문제**: `_playback_thread`, `_stop_flag`, `_pause_flag`, `_current_event_idx`, `_total_events`가 모듈 전역. `stop()` 후 즉시 `play()` 호출 시 두 PlaybackThread 동시 실행 가능. `get_progress()`에서 `_total_events=0` 초기화와 읽기 레이스 시 ZeroDivisionError.
- **수정 방향**: `PlaybackController` 클래스로 캡슐화. 공개 인터페이스(`play`, `stop`, `pause`, `resume`, `is_playing`, `get_progress`, `is_stopping`)를 메서드로 유지하여 기존 호출부 영향 최소화.

---

**8. [main_window.py:전체] — God Class (SRP 위반, 1,086줄)** `[아키텍처 ARCH-02]`

- **문제**: 상태머신·Win32 핫키·파일 I/O·반복 재생 스레드·오버레이·최근 파일 관리 등 6개 이상 책임 집중. 단위 테스트 사실상 불가(테스트 가능성 ⭐).
- **수정 방향 (단계적)**:
  - 1단계: `_reset_playback_state()` 헬퍼 추출 (현재 3곳 중복 5줄 제거, 즉시 적용 가능)
  - 2단계: `PlaybackManager` 분리 (`_repeat_worker` 클로저 포함)
  - 3단계: `HotkeyManager`, `FileManager` 분리 (다음 PR)

---

**9. [main_window.py:536,560,572] — player._stop_flag 직접 접근 (캡슐화 위반)** `[스타일 🔴 + 아키텍처 ARCH-03 — 중복 통합]`

- **문제**: UI 레이어가 `player._stop_flag.is_set()`를 3곳에서 직접 참조. `# type: ignore[attr-defined]`로 타입 시스템을 우회. `player.py` 리팩토링 시 UI도 동시 수정 필요.
- **수정 방향**: `player.py`에 `is_stopping() -> bool` 공개 함수(또는 `PlaybackController.is_stopping()` 메서드) 추가 후 대체. `# type: ignore` 제거.

---

### 🟡 머지 후 수정 (다음 PR에서)

1. **[macro_file.py:63-145] — JSON 역직렬화 값 범위 검증 없음** `[보안 MED-01]`
   - `x_ratio`/`y_ratio` 0.0~1.0 클램핑, `vk_code` 위험 키 차단(Win_L, Win_R, PrintScreen), `timeout_ms`/`duration_ms` 상한 적용

2. **[script_engine.py:492] — 자원 고갈 방지 누락** `[보안 MED-02]`
   - `WaitFixedNode.duration_ms` 상한(1시간), `CounterNode.max` 상한(10,000), `increment > 0` 검증 (현재 0이면 무한루프)

3. **[player.py:149-154] — LoopEvent 중첩 깊이 무제한** `[보안 MED-04]`
   - `_execute_event()`에 `depth: int = 0` 파라미터 추가, `MAX_NESTING_DEPTH = 32` 초과 시 `PlaybackError`

4. **[sequencer.py:257-268] — 파일명 부분 일치 오매핑** `[보안 MED-03 / 스타일·아키텍처 중복]`
   - `QListWidgetItem.setData(UserRole, str(path))` 저장 후 정확한 경로 기반 매핑으로 교체

5. **[editor.py:110-322] — _build_rows() O(N²) 내부 루프** `[성능 🟡]`
   - 전처리 `up_map: dict[int, int]` 생성으로 O(N) 개선. 1만 이벤트 기준 빌드 시간 100ms → 5ms 예상

6. **[editor.py:578-596] — highlight_event() O(N) 선형 탐색** `[성능 🟡]`
   - `_refresh()` 시점에 `_event_to_row: dict[int, int]` 역인덱스 빌드 → O(1) 조회

7. **[player.py:263] — list(enumerate(all_events))[start:end] 전체 복사** `[성능 🟡]`
   - `list(enumerate(all_events[start:end], start=start))`로 교체 (코드 1줄, 트레이드오프 없음)

8. **[recorder.py:224-248] — _consumer_loop 1ms busy-wait** `[성능 🟡]`
   - `time.sleep(0.001)` → `time.sleep(0.005)` 또는 `queue.SimpleQueue.get(timeout=0.005)` 패턴으로 대체

9. **[recorder.py:326] — DPI 스케일 수작업 추정값 사용** `[스타일 🔴]`
   - `_screen_w / 1920.0` → `get_dpi_scale()` (이미 임포트 가능, 1줄 수정)

10. **[hooks.py:185,197] — Win32 콜백 camelCase ruff N803** `[스타일 🔴]`
    - 파일 상단에 `# ruff: noqa: N803` 추가 및 Win32 콜백 시그니처 규약 주석 명시

11. **[sequencer.py:183-184] — 인스턴스 메서드 직접 패치** `[스타일 🔴]`
    - `QListWidget` 서브클래싱으로 `dragEnterEvent`/`dropEvent` 오버라이드

12. **[main_window.py:545] — 라인 길이 초과 E501** `[스타일 🔴]`
    - `_on_error` 시그니처를 다줄 포맷으로 분리

13. **[player.py:275-276] — 일시정지 50ms sleep 폴링** `[성능 🟡]`
    - `_resume_event: threading.Event` 추가 → `wait(timeout=0.05)` 패턴으로 resume 응답 50ms → <1ms

14. **[player.py / script_engine.py] — _hex_to_rgb / _color_matches 중복** `[아키텍처 🟡 / 스타일·성능 중복]`
    - `macroflow/utils/color.py`로 추출하거나 `types.py` 유틸리티로 통합

15. **[main_window.py] — 상태 문자열 리터럴 직접 비교** `[스타일 🟡]`
    - `_state: str` → `_state: Literal["idle", "recording", "stopping", "playing"]` 또는 `StrEnum`

16. **[recorder.py:371] — get_event_count() 락 미사용** `[보안 LOW-03 / 성능·스타일 중복]`
    - `with _event_buffer_lock: return len(_event_buffer)` 로 명시적 스레드 안전성 보장

---

### 🟢 개선 제안 (팀 논의)

1. **[player.py / recorder.py] — PlaybackController / RecordingSession 클래스화** — ARCH-01 수정과 연계. recorder.py는 우선순위 낮으나 player.py와 일관성 확보를 위해 동시 리팩토링 권장.

2. **[script_engine.py] — FlowEngine / inline_executor 분리** — `flow_engine.py`(FlowEngine + 노드 타입)와 `inline_executor.py`(execute_condition, execute_loop)로 분리하면 지연 임포트 패턴을 정리할 수 있음.

3. **[macro_file.py] — 편집 유틸리티를 macro_ops.py로 분리** — `load`/`save`(파일 I/O)와 순수 변환 함수 혼재 해소.

4. **[win32/hotkey.py 신설] — RegisterHotKey Win32 래퍼 추가** — `main_window.py`에서 `ctypes.windll.user32.RegisterHotKey` 직접 호출을 win32 레이어로 이동.

5. **[GitHub Releases] — SHA-256 체크섬 파일 첨부** — 코드 서명 전 단기 대안. `보안 LOW-01` 대응.

6. **[main.py] — 로그 파일명에 PID 추가** — `macroflow_{ts}_{os.getpid()}.log` 패턴으로 동시 실행 시 충돌 방지. `보안 LOW-02` 대응.

7. **[win32/hooks.py, sendinput.py, dpi.py] — assert → ImportError** — `python -O` 최적화 모드에서 assert 비활성화 문제 해소. `스타일 🟡` 대응.

8. **[player.py:275-276] — timeBeginPeriod(1) 도입 검토** — Windows 기본 타이머 해상도 15.6ms → 1ms 개선. 시스템 전체 영향 있으므로 팀 논의 필요.

---

## 영역별 요약

| 영역 | 판정 | 🔴 | 🟡 | 핵심 발견 | 자동화 가능 |
|---|---|---|---|---|---|
| **스타일** | 🔴 요수정 | 8 | 18 | player._stop_flag 캡슐화 위반, N803 noqa 미기재, DPI 추정값 방치, 메서드 직접 패치 | ruff로 E501·N803 자동 검출 가능 |
| **보안** | 🔴 요수정 | Critical 1 / High 2 | Medium 4 | eval() RCE, 절대 경로 Path Traversal, DEBUG 로그 민감 정보 | AST 검증 자동화 가능, 나머지는 수동 |
| **성능** | 🟡 개선 여지 | 3 | 6 | drag sleep 100ms 드리프트, GDI 핸들 누수, normalize syscall 반복 | 일부 정적 분석으로 sleep 패턴 검출 가능 |
| **아키텍처** | 🟡 개선 필요 | 3 | 6 | God Class 1,086줄, 전역 상태 경쟁 조건, private 접근 강결합 | 자동화 불가 (설계 판단 필요) |

---

## 영역 간 충돌 해결

| 충돌 | 영역1 주장 | 영역2 주장 | 판정 | 근거 |
|---|---|---|---|---|
| **eval() 처리 방향** | 보안: eval 제거 후 DSL 파서 구현 | 스타일: 현재 샌드박스 구조가 의도 명확하다고 칭찬 | **AST 화이트리스트 검증 추가 (eval 유지)** | eval 완전 제거는 ConditionEvent 기능 회귀. AST 검증으로 현실적 보안 강화 가능. DSL 파서는 장기 로드맵. |
| **drag sleep 제거 vs 안정성** | 성능: sleep 제거 + SendInput 배치 | 암묵적 안정성: 일부 앱은 이동 딜레이 필요 | **sleep 제거 + `drag_step_delay_ms=0` 옵션 파라미터** | core-beliefs 원칙 3 위반이므로 기본값은 반드시 0. 특수 케이스는 옵션으로 제공. |
| **player._stop_flag 접근** | 스타일: 🔴 캡슐화 위반 | 아키텍처: 🔴 동일 문제 ARCH-03으로 분류 | **단일 항목으로 통합 (🔴 #9)** | 양 영역 동일 지적. `is_stopping()` 공개 함수 추가로 해결. |
| **ARCH-01 전역 상태 리팩토링 규모** | 아키텍처: PlaybackController 클래스화 권고 | 성능: 동시성 경쟁 조건 별도 지적 | **리팩토링 필요, 이번 PR 범위에 포함** | 경쟁 조건(두 스레드 동시 실행)은 실제 버그이므로 머지 차단 수준. 클래스화로 근본 해결. |
| **CounterNode._value 위치** | 스타일: dataclass 필드 분리 | 아키텍처: 동일 문제 지적 | **FlowEngine 내부 dict로 분리** | `asdict()` 오염 방지 + 런타임 상태 격리. |
| **get_event_count() 락 적용** | 보안: `_event_buffer_lock` 일관 적용 | 성능: CPython GIL 보호 범위 내 | **락 적용** | 성능 오버헤드 무시 가능(250ms 폴링). 코드 의도 명확화 효과 우선. |

---

## 액션 아이템 (우선순위순, 상위 10개)

| # | 항목 | 우선순위 | 예상 시간 | 담당 영역 | 비고 |
|---|---|---|---|---|---|
| 1 | eval() AST 화이트리스트 검증 추가 (`script_engine.py:544`) | 🔴 긴급 | 2h | 보안 | expression 길이 상한 + Attribute 노드 거부 포함 |
| 2 | 절대 경로 Path Traversal 검증 (`script_engine.py:401`) | 🔴 긴급 | 1h | 보안 | `is_relative_to()` 한 줄 추가 |
| 3 | DEBUG → INFO 로그 레벨 조정 + expression 로그 제거 | 🔴 긴급 | 1h | 보안 | `main.py` + `script_engine.py` 2파일 수정 |
| 4 | GDI 핸들 누수 수정 (`hooks.py:379`, try/finally) | 🔴 긴급 | 0.5h | 성능 | 코드 3줄 변경, 트레이드오프 없음 |
| 5 | drag sleep 제거 + SendInput 배치 (`sendinput.py:184`) | 🔴 긴급 | 2h | 성능 | `drag_step_delay_ms=0` 옵션 파라미터 포함 |
| 6 | `player.is_stopping()` 공개 함수 추가 + private 접근 제거 | 🔴 높음 | 1h | 스타일/아키텍처 | 3곳 `type: ignore` 제거 연계 |
| 7 | `PlaybackController` 클래스화 (`player.py`) | 🔴 높음 | 4~6h | 아키텍처 | 동시성 버그 근본 해결. 기존 API 시그니처 유지 |
| 8 | `_normalize()` 화면 크기 캐싱 (`sendinput.py:110`) | 🟡 중간 | 1h | 성능 | 해상도 변경 이벤트 구독 포함 |
| 9 | `_build_rows()` O(N²) → O(N) 개선 (`editor.py:110`) | 🟡 중간 | 2h | 성능 | `up_map` 전처리 도입 |
| 10 | JSON 역직렬화 범위 검증 추가 (`macro_file.py:63`) | 🟡 중간 | 2h | 보안 | `x_ratio`, `vk_code`, `timeout_ms` 상한/차단 |

---

## 칭찬할 점

1. **절대 타임스탬프 재생 + 드리프트 보정 설계**: `play_start_ns` 전진 보정으로 색/창 트리거 실제 대기 시간을 흡수하는 메커니즘이 정교하다. `last_significant_event_end_ns` 클램프로 음수 딜레이 역전까지 처리한 세밀함이 돋보인다.

2. **win32 레이어 완성도**: `LRESULT = ctypes.c_ssize_t`, `argtypes`/`restype` 완전 선언, `LLKHF_INJECTED` 플래그 필터링 등 Win32 API를 방어적으로 다루는 수준이 높다. 64비트 호환성 이유를 인라인 주석으로 명시한 점도 우수.

3. **코딩 컨벤션 준수도**: `from __future__ import annotations` 일관 적용, `# ── 섹션명 ──` 구분 주석 통일, `core-beliefs.md 원칙 N` 인라인 참조 등 팀 컨벤션이 코드 전반에 내재화되어 있다.

4. **types.py 독립성**: Win32·PyQt6 의존성이 전혀 없는 순수 데이터 레이어. 데이터 모델과 플랫폼 코드 분리가 명확하며 어떤 환경에서도 임포트 가능.

5. **불변 데이터 패턴**: `macro_file.py` 편집 함수들이 원본 `MacroData`를 수정하지 않고 항상 새 인스턴스를 반환하는 함수형 패턴을 일관되게 사용. `raw_events` 불변 원칙도 코드에 반영됨.

6. **Qt Signal/Slot 스레드 경계 처리**: 워커 스레드에서 직접 UI를 건드리지 않고 `pyqtSignal`로 메인 스레드에 안전하게 전달하는 구조가 일관되게 지켜진다. `_sig_recording_done`, `_sig_play_complete` 등이 모범 사례.

7. **의존성 선택**: pynput을 의도적으로 배제하고 Win32 LL Hook을 직접 구현한 선택이 이벤트 순서 보장 문제를 근본적으로 해결했다. `uv.lock` 버전 고정으로 의존성 위험도 낮다.

---

## 최종 산출물 체크리스트

### 머지 전 필수 완료 항목
- [ ] eval() AST 화이트리스트 검증 구현 (`script_engine.py:544`)
- [ ] 절대 경로 Path Traversal 검증 추가 (`script_engine.py:401`)
- [ ] DEBUG → INFO 로그 레벨 조정 + expression 로그 제거
- [ ] GDI 핸들 누수 수정 (`hooks.py:379`, try/finally)
- [ ] drag sleep 제거 + SendInput 배치 (`sendinput.py:184`)
- [ ] `player.is_stopping()` 공개 함수 추가 + private 접근 3곳 제거
- [ ] `PlaybackController` 클래스화 (`player.py`)

### 다음 PR 등록 항목
- [ ] JSON 역직렬화 범위 검증 (`macro_file.py:63`)
- [ ] 자원 고갈 방지 — increment 검증, 값 상한 (`script_engine.py:492`)
- [ ] LoopEvent 중첩 깊이 제한 (`player.py:149`, MAX_NESTING_DEPTH=32)
- [ ] sequencer.py UserRole 기반 매핑 (`sequencer.py:257`)
- [ ] `_build_rows()` O(N²) → O(N) 개선 (`editor.py:110`)
- [ ] `highlight_event()` O(N) → O(1) 역인덱스 (`editor.py:578`)
- [ ] `_normalize()` 화면 크기 캐싱 (`sendinput.py:110`)
- [ ] `_hex_to_rgb`/`_color_matches` 공통 모듈로 추출
- [ ] `get_event_count()` 락 적용 (`recorder.py:371`)
- [ ] DPI 스케일 추정값 → `get_dpi_scale()` 교체 (`recorder.py:326`)

### 리팩터링 마일스톤 등록 항목 (`tech-debt-tracker.md`)
- [ ] `MainWindow` God Class 책임 분리 (PlaybackManager, HotkeyManager, FileManager)
- [ ] `recorder.py` → `RecordingSession` 클래스화
- [ ] `script_engine.py` → `flow_engine.py` + `inline_executor.py` 분리
- [ ] `macro_file.py` → `macro_ops.py` 편집 유틸리티 분리
- [ ] `win32/hotkey.py` 신설 (RegisterHotKey 래퍼)

---

## 리뷰 완료 상태

- [x] 스타일 리뷰 완료 (🔴 8 / 🟡 18 / 🟢 9)
- [x] 보안 리뷰 완료 (Critical 1 / High 2 / Medium 4 / Low 5)
- [x] 성능 리뷰 완료 (🔴 3 / 🟡 6 / 🟢 3)
- [x] 아키텍처 리뷰 완료 (🔴 3 / 🟡 6 / 🟢 4)
- [x] 영역 간 충돌 해결 (6개 충돌 분석 및 판정)
- [x] 액션 아이템 생성 (상위 10개, 우선순위·예상 시간 포함)
