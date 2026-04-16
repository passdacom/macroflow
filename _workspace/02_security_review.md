# 보안 리뷰 — MacroFlow v0.2.0

> 분석 일자: 2026-04-14 (갱신)  
> 분석 기준: OWASP Top 10 (2021), CWE, 내부 SECURITY.md  
> 분석 범위: script_engine.py, macro_file.py, win32/hooks.py, win32/sendinput.py, recorder.py, player.py, ui/main_window.py, ui/favorites.py, ui/sequencer.py, pyproject.toml

---

## 리뷰 개요

- **보안 수준 평가**: 🟡 보통 (내부 배포 도구 기준 양호, 그러나 eval() 샌드박스 우회 가능성 존재)
- **총 발견 수**: Critical 1 / High 2 / Medium 4 / Low 5

---

## 취약점 발견 사항

### 🔴 Critical / High

---

#### [CRIT-01] eval() 샌드박스 탈출 — Python 객체 그래프 순회 공격 (script_engine.py:544)

**심각도**: Critical  
**CWE**: CWE-94 (코드 인젝션), CWE-78 (OS 명령 인젝션)  
**OWASP**: A03:2021 – 인젝션

**위치**: `src/macroflow/script_engine.py`, `execute_condition()`, 544행

```python
sandbox_globals: dict[str, Any] = {
    "__builtins__": {},          # ← builtins 차단 시도
    "pixel_color": _pixel_color,
    "wait": _wait,
    "random": _random,
    "True": True,
    "False": False,
}
result = bool(eval(event.expression, sandbox_globals))
```

**문제점**:  
`__builtins__` 를 빈 딕셔너리 `{}`로 설정하는 방식은 Python의 표준 샌드박스 탈출 방어 기법이지만, Python 객체 그래프 순회(attribute traversal)로 완전히 우회된다.

**공격 예시**:
```python
# ().__class__.__bases__[0].__subclasses__() → object 서브클래스 전체 접근
# pixel_color.__class__.__init__.__globals__ → 전역 네임스페이스 접근
# → os, subprocess, ctypes 등 임의 모듈 획득 가능

pixel_color.__class__.__mro__[-1].__subclasses__()
# 또는
().__class__.__base__.__subclasses__()[X].__init__.__globals__['os'].system('cmd')
```

악의적인 `.json` 매크로 파일의 `ConditionEvent.expression` 필드에 위 표현식을 삽입하면, 파일을 여는 즉시 임의 코드가 실행된다.

**영향**:  
- 임의 파일 읽기/쓰기/실행  
- 시스템 명령 실행 (os.system, subprocess)  
- 원격 코드 실행(RCE) 가능

**수정 방안**:
```python
# 방안 1: AST 파싱으로 허용 노드만 화이트리스트 검증 후 eval
import ast

ALLOWED_NODES = {
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp,
    ast.Compare, ast.Call, ast.Constant, ast.Name,
    ast.And, ast.Or, ast.Not, ast.Eq, ast.NotEq,
    ast.Lt, ast.LtE, ast.Gt, ast.GtE,
}
ALLOWED_FUNC_NAMES = {"pixel_color", "wait", "random"}

def _validate_expression(expr: str) -> None:
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise ValueError(f"허용되지 않은 AST 노드: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNC_NAMES:
                raise ValueError(f"허용되지 않은 함수 호출")
        if isinstance(node, ast.Attribute):
            raise ValueError("속성 접근(attribute access) 금지")

# 방안 2: DSL을 별도 파서로 구현 (eval 완전 제거 — 가장 안전)
```

---

#### [HIGH-01] 절대 경로 경유 Path Traversal 우회 — MacroNode.macro_path (script_engine.py:401~426)

**심각도**: High  
**CWE**: CWE-22 (경로 조작)  
**OWASP**: A01:2021 – 접근 제어 취약

**위치**: `src/macroflow/script_engine.py`, `_run_macro_node()`, 401~426행

```python
raw = Path(node.macro_path)
if raw.is_absolute():
    # 절대 경로: 시퀀서가 직접 생성한 경로이므로 그대로 사용  ← 취약
    macro_path = raw
else:
    # 상대 경로: Path Traversal(../) 방지 검사 적용
    macro_path = (self._base_dir / raw).resolve()
    if not macro_path.is_relative_to(self._base_dir.resolve()):
        raise FlowError(...)
```

**문제점**:  
절대 경로는 검증 없이 그대로 사용된다. 악의적인 `.macroflow` 파일에서 `macro_path`를 `C:\Windows\System32\evil.json`으로 지정하거나, 존재하지 않는 UNC 경로(`\\attacker\share\payload.json`)를 지정하면 경계 밖 파일에 접근할 수 있다. 또한 "시퀀서가 직접 생성한 경로"라는 가정은 `.macroflow` 파일이 외부에서 유입될 경우 깨진다.

**영향**:  
- 시스템의 임의 위치에 있는 JSON 파일 로드 및 실행  
- 네트워크 경로를 통한 원격 페이로드 로드 가능  
- 악성 `.macroflow` 파일 공유를 통한 피해 확산 (팀 내 배포 환경)

**수정 방안**:
```python
def _run_macro_node(self, node: MacroNode) -> str | None:
    raw = Path(node.macro_path)
    if raw.is_absolute():
        macro_path = raw.resolve()
    else:
        macro_path = (self._base_dir / raw).resolve()
    
    # 절대 경로도 허용된 기준 디렉토리 내로 제한
    allowed_roots = [self._base_dir.resolve()]
    # 필요 시 허용 루트 확장: 사용자 지정 매크로 디렉토리 등
    if not any(macro_path.is_relative_to(r) for r in allowed_roots):
        raise FlowError(f"보안: 허용 디렉토리 외부 경로 차단 ({node.macro_path!r})")
```

---

#### [HIGH-02] 민감 정보 로그 파일 기록 — 키 입력 내용 유출 (macro_file.py, recorder.py)

**심각도**: High  
**CWE**: CWE-312 (민감 정보 평문 저장), CWE-532 (로그에 민감 정보 노출)  
**OWASP**: A02:2021 – 암호화 실패

**위치**:  
- `src/macroflow/main.py`, 36~42행: `logging.basicConfig(level=logging.DEBUG, ...)`  
- `src/macroflow/recorder.py`, 355행: `logger.info(f"ColorTriggerEvent 삽입: {color_hex} @ ...")`  
- `src/macroflow/script_engine.py`, 544행: `logger.error(f"ConditionEvent 표현식 오류 ({event.expression!r}): {e}")`  
- JSON 파일: `KeyEvent.key` 필드에 키 이름 평문 저장 (`macro_file.py`)

**문제점**:

1. **로그 레벨이 `DEBUG`로 고정**되어 있어 재생 중 모든 이벤트, 경로, 표현식 내용이 `%LOCALAPPDATA%\MacroFlow\logs\` 에 기록된다.
2. **ConditionEvent 오류 로그**에 expression 전체가 출력된다. expression에 비밀번호, API 키 등이 포함된 경우 로그에 평문 노출.
3. **KeyEvent.key 필드**에 사용자가 입력한 키 이름이 저장된다. SECURITY.md도 이를 인지하고 있으나 현재 기술적 보호 수단이 없다.
4. 로그 파일 접근 권한 설정 없음 — 같은 PC의 다른 로그인 사용자가 접근 가능.

**수정 방안**:
```python
# main.py — 배포 빌드에서 INFO 레벨로 조정
log_level = logging.DEBUG if os.environ.get("MACROFLOW_DEBUG") else logging.INFO
logging.basicConfig(level=log_level, ...)

# script_engine.py — expression 내용 로그에서 제거
logger.error(f"ConditionEvent 표현식 오류 (expression 생략): {type(e).__name__}: {e}")

# macro_file.py — 민감 필드 마스킹 고려 (향후 Phase2)
# 단기: 비밀번호 입력 구간 사용 안내를 UI에 표시
```

---

### 🟡 Medium

---

#### [MED-01] JSON 역직렬화 — 타입 및 값 범위 검증 부재 (macro_file.py)

**심각도**: Medium  
**CWE**: CWE-20 (입력 검증 부재)  
**OWASP**: A03:2021 – 인젝션

**위치**: `src/macroflow/macro_file.py`, `_dict_to_event()`, 63~145행

**문제점**:  
JSON 로드 시 필드 타입·범위 검증이 없다. 예를 들어:
- `x_ratio`, `y_ratio` : 0.0~1.0 범위 초과 값 허용 → 화면 밖 좌표로 SendInput 전송
- `timeout_ms` : 음수나 매우 큰 값 허용 → 무한 대기 또는 즉시 타임아웃
- `vk_code` : 임의 가상 키 코드 허용 → 예상치 못한 시스템 키(Win, PrintScreen 등) 전송
- `duration_ms` : 음수 허용 → `time.sleep` 에 음수 전달 시 즉시 반환 (이상 동작)
- `count` (LoopEvent) : `-1` 외 음수 허용 → 언더플로우 시 무한 루프 가능

```python
# 현재: 검증 없음
return MouseButtonEvent(
    **common,
    x_ratio=d["x_ratio"],   # -999.0 등 허용
    y_ratio=d["y_ratio"],
    button=d.get("button", "left"),  # 임의 문자열 허용
)
```

**수정 방안**:
```python
def _validate_ratio(v: float, name: str) -> float:
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{name} 범위 초과: {v}")
    return v

def _validate_vk_code(v: int) -> int:
    BLOCKED_VK = {0x5B, 0x5C, 0x2C}  # Win_L, Win_R, PrintScreen
    if v in BLOCKED_VK:
        raise ValueError(f"차단된 VK 코드: {v:#04x}")
    if not (1 <= v <= 254):
        raise ValueError(f"유효하지 않은 VK 코드: {v}")
    return v
```

---

#### [MED-02] WaitFixedNode / ColorCheckNode 자원 고갈 (script_engine.py)

**심각도**: Medium  
**CWE**: CWE-400 (자원 고갈), CWE-834 (과도한 반복)  
**OWASP**: A05:2021 – 보안 설정 오류

**위치**: `src/macroflow/script_engine.py`, `_run_color_check_node()`, `_run_counter_node()`

**문제점**:
1. `WaitFixedNode.duration_ms` 에 상한 없음 → JSON에 `duration_ms: 2147483647` 설정 시 25일 이상 대기
2. `CounterNode.max` 에 상한 없음 → `max: 2147483647`로 설정 시 사실상 무한 루프  
3. `ColorCheckNode.timeout_ms` 에 상한 없음 → 동일 문제
4. `CounterNode.increment` 에 검증 없음 → `increment: 0` 설정 시 `_value >= max` 조건 절대 미충족 → 무한 루프

```python
# script_engine.py:492
node._value += node.increment   # increment=0이면 영원히 루프
reached = node._value >= node.max
```

**수정 방안**:
```python
# JSON 로드 시 상한 검증
MAX_WAIT_MS = 3_600_000      # 1시간
MAX_TIMEOUT_MS = 300_000     # 5분
MAX_LOOP_COUNT = 10_000

if d.get("duration_ms", 1000) > MAX_WAIT_MS:
    raise ValueError(f"duration_ms 초과: {d['duration_ms']}")
if d.get("increment", 1) <= 0:
    raise ValueError("increment는 양수여야 합니다")
```

---

#### [MED-03] _sync_items_from_list — 파일명 부분 일치로 잘못된 항목 매핑 (ui/sequencer.py:257~268)

**심각도**: Medium  
**CWE**: CWE-706 (잘못된 리소스 해석)  
**OWASP**: A04:2021 – 불안전한 설계

**위치**: `src/macroflow/ui/sequencer.py`, `_sync_items_from_list()`, 257~268행

```python
for item in self._items:
    if item.path.name in text:   # ← 부분 문자열 일치
        new_items.append(item)
        break
```

**문제점**:  
`item.path.name`이 다른 항목의 표시 텍스트에 부분 포함될 경우 잘못된 매핑이 발생한다.  
예: `test.json`과 `big_test.json`이 함께 있을 때 드래그 재정렬 후 순서가 뒤바뀔 수 있다.  
악의적이지는 않지만 실행 순서 혼동으로 의도치 않은 매크로가 실행될 수 있다.

**수정 방안**:
```python
# QListWidgetItem에 path를 UserRole 데이터로 저장하여 정확히 매핑
list_item.setData(Qt.ItemDataRole.UserRole, str(item.path))

# sync 시
for i in range(self._list.count()):
    li = self._list.item(i)
    stored_path = li.data(Qt.ItemDataRole.UserRole)
    matching = next((it for it in self._items if str(it.path) == stored_path), None)
    if matching:
        new_items.append(matching)
```

---

#### [MED-04] LoopEvent 무한 재귀 — 중첩 ConditionEvent/LoopEvent 스택 오버플로우 (player.py:149~154)

**심각도**: Medium  
**CWE**: CWE-674 (과도한 재귀), CWE-400 (자원 고갈)  
**OWASP**: A05:2021 – 보안 설정 오류

**위치**: `src/macroflow/player.py`, `_execute_event()`, 149~154행

```python
elif isinstance(event, ConditionEvent):
    execute_condition(event, _stop_flag, lambda e: _execute_event(e, settings, state))

elif isinstance(event, LoopEvent):
    execute_loop(event, _stop_flag, lambda e: _execute_event(e, settings, state))
```

**문제점**:  
중첩 깊이 제한이 없다. JSON에서 LoopEvent 내 LoopEvent를 수백 단계 중첩하면 Python 스택 오버플로우(RecursionError)가 발생한다. 또한 ConditionEvent.if_true 내에 동일 ConditionEvent를 재귀적으로 삽입하면 `_dict_to_event()`가 스택을 소진할 수 있다.

**수정 방안**:
```python
# _execute_event에 depth 파라미터 추가
MAX_NESTING_DEPTH = 32

def _execute_event(event, settings, state, depth=0):
    if depth > MAX_NESTING_DEPTH:
        raise PlaybackError(f"이벤트 중첩 깊이 초과 ({MAX_NESTING_DEPTH})")
    ...
    execute_condition(event, _stop_flag, 
        lambda e: _execute_event(e, settings, state, depth + 1))
```

---

### 🟢 Low / Informational

---

#### [LOW-01] 코드 서명(Code Signing) 없이 팀 배포 — SmartScreen 우회 위험

**심각도**: Low  
**CWE**: CWE-345 (무결성 검증 부재)  
**OWASP**: A08:2021 – 소프트웨어 및 데이터 무결성 실패

SECURITY.md에서 SmartScreen 경고를 "정상적인 현상"으로 안내하고 있다. 코드 서명이 없으면 공격자가 악의적인 `MacroFlow.exe`를 정상 파일로 위장하여 배포 채널에 삽입할 때 팀원이 구분하기 어렵다. 내부 배포이므로 즉각적인 위협은 낮으나 체크섬 검증이라도 제공해야 한다.

**권고**: GitHub Releases 페이지에 SHA-256 체크섬 파일 첨부. 장기적으로 코드 서명 인증서 취득 검토.

---

#### [LOW-02] 로그 파일 경로에 타임스탬프만 사용 — 동시 실행 시 경쟁 조건

**심각도**: Low  
**CWE**: CWE-377 (안전하지 않은 임시 파일)

**위치**: `src/macroflow/main.py`, 34행

```python
log_file = log_dir / f"macroflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
```

같은 초에 두 번 실행되면 동일 로그 파일 경로가 생성된다 (단일 사용자 앱이므로 실제 위험 낮음). 또한 로그 파일에 파일 시스템 ACL 설정이 없어 동일 PC의 다른 사용자가 읽을 수 있다.

**권고**: 파일명에 PID 추가 (`macroflow_{ts}_{os.getpid()}.log`). 로그 파일 생성 후 소유자만 읽기 권한으로 제한.

---

#### [LOW-03] get_event_count() — 락 없는 공유 변수 접근 (recorder.py:363)

**심각도**: Low  
**CWE**: CWE-366 (경쟁 조건)

**위치**: `src/macroflow/recorder.py`, 363행

```python
def get_event_count() -> int:
    return len(_event_buffer)    # ← _event_buffer_lock 없이 접근
```

`_event_buffer`는 `_event_buffer_lock`으로 보호되어야 하지만 `get_event_count()`는 락 없이 접근한다. 폴링 타이머(250ms)에서 호출되므로 실제 데이터 손상 위험은 낮지만 GIL 보호 범위 외에서 이상 동작 가능성이 있다.

---

#### [LOW-04] main_window.py — ctypes.wintypes.MSG.from_address() 안전성

**심각도**: Low  
**CWE**: CWE-119 (메모리 접근 오류)

**위치**: `src/macroflow/ui/main_window.py`, 340행

```python
msg = ctypes.wintypes.MSG.from_address(int(message))
```

`nativeEvent`에서 전달받은 `message` 포인터를 `from_address()`로 역참조한다. PyQt6 문서에 따르면 Windows에서 `event_type == b"windows_generic_MSG"`일 때 포인터가 유효하지만, 향후 Qt 버전 업그레이드 시 메모리 레이아웃이 변경될 경우 크래시 위험이 있다. `ctypes.cast` 또는 `sip.voidptr` 방식이 더 안전하다.

---

#### [LOW-05] __temp_sequence__.macroflow — 임시 파일 미정리 (ui/sequencer.py:484)

**심각도**: Low  
**CWE**: CWE-377 (안전하지 않은 임시 파일)

**위치**: `src/macroflow/ui/sequencer.py`, 484행

```python
temp_flow_path = flow_base / "__temp_sequence__.macroflow"
flow = self._build_flow(temp_flow_path)
# ← 파일 시스템에 실제로 쓰이지는 않지만 경로가 FlowEngine에 전달됨
```

`_build_flow()`는 파일을 실제로 저장하지 않고 경로 계산에만 사용한다. 그러나 `FlowEngine`의 `_base_dir`이 이 가상 경로 기반으로 설정되므로 `__temp_sequence__.macroflow`가 실수로 파일 시스템에 쓰이면 정리되지 않는다. 명시적 임시 디렉토리(`tempfile.mkdtemp`) 사용을 권고한다.

---

## OWASP Top 10 매핑

| OWASP Top 10 (2021) | 해당 취약점 | 위험도 |
|---|---|---|
| **A01: 접근 제어 취약** | HIGH-01 절대경로 Path Traversal 우회 | 🔴 High |
| **A02: 암호화 실패** | HIGH-02 민감 정보 DEBUG 로그 기록 | 🔴 High |
| **A03: 인젝션** | CRIT-01 eval() 샌드박스 탈출, MED-01 JSON 입력 검증 부재 | 🔴 Critical / 🟡 Medium |
| **A04: 불안전한 설계** | MED-03 파일명 부분 일치 매핑 | 🟡 Medium |
| **A05: 보안 설정 오류** | MED-02 자원 고갈 (무한루프), MED-04 재귀 깊이 무제한 | 🟡 Medium |
| **A06: 취약하고 오래된 컴포넌트** | 해당 없음 (PyQt6, uv.lock 사용) | 🟢 해당 없음 |
| **A07: 인증 및 인증 실패** | 해당 없음 (단일 사용자 로컬 앱) | 🟢 해당 없음 |
| **A08: 소프트웨어 무결성 실패** | LOW-01 코드 서명 없음 | 🟢 Low |
| **A09: 로깅 및 모니터링 실패** | HIGH-02 과도한 DEBUG 로깅 | 🔴 High |
| **A10: SSRF** | 해당 없음 (네트워크 요청 없음) | 🟢 해당 없음 |

---

## 의존성 취약점

| 패키지 | 버전 요구사항 | 알려진 CVE | 비고 |
|---|---|---|---|
| PyQt6 | >=6.6.0 | 없음 (2026-04 기준) | Qt 6.6~6.8 범위, 정기 업데이트 권고 |
| Python ctypes | 표준 라이브러리 | 없음 | OS 의존, Python 버전과 동기화 |
| hatchling (빌드) | 빌드 의존성만 | 없음 | 런타임 영향 없음 |
| pytest / ruff / mypy / pyinstaller | dev 의존성 | 없음 | 배포 바이너리에 미포함 |

> **전반적으로 의존성 위험은 낮음.** `uv.lock` 파일로 버전 고정되어 있으며, pynput 같은 고위험 서드파티를 의도적으로 배제한 설계.  
> 단, PyInstaller 6.x 빌드 바이너리에 번들된 Python 런타임은 주기적 업데이트 필요.

---

## 보안 강화 권고

### 우선순위 1 (즉시 조치 필요)

1. **eval() 샌드박스 강화 (CRIT-01)**  
   - 단기: `ast.parse()` + 허용 노드 화이트리스트로 expression 사전 검증  
   - 장기: DSL 파서를 별도 구현하여 `eval()` 완전 제거  
   - `expression` 필드 길이 상한 설정 (예: 1,000자)

2. **절대 경로 검증 추가 (HIGH-01)**  
   - `_run_macro_node()`에서 절대 경로도 허용 루트 목록 내에서만 허용  
   - 기준 디렉토리는 앱 시작 시 명시적으로 정의 (예: `~/MacroFlow/macros/`)

3. **로그 레벨 조정 (HIGH-02)**  
   - 배포 빌드: `INFO` 레벨 기본 설정, `--debug` 플래그로만 `DEBUG` 활성화  
   - ConditionEvent 오류 로그에서 expression 내용 제거  
   - 로그 파일 Windows ACL 설정 (`os.chmod(log_file, 0o600)` 등)

### 우선순위 2 (단기 개선)

4. **JSON 입력 검증 강화 (MED-01)**  
   - `x_ratio`, `y_ratio`: 0.0~1.0 클램핑 또는 예외  
   - `vk_code`: 위험 키 코드 차단 목록 (Win, PrintScreen, Task Manager 등)  
   - `timeout_ms`, `duration_ms`: 상한 적용

5. **자원 소진 방지 (MED-02, MED-04)**  
   - `WaitFixedNode`, `ColorCheckNode`, `CounterNode` 값 상한 검증  
   - 이벤트 중첩 깊이 제한 (`MAX_NESTING_DEPTH = 32`)

6. **_sync_items_from_list 매핑 수정 (MED-03)**  
   - `QListWidgetItem.setData(UserRole, path_str)` 로 정확한 매핑

### 우선순위 3 (장기 개선)

7. **코드 서명 도입 (LOW-01)**  
   - 단기: GitHub Releases에 SHA-256 체크섬 첨부  
   - 장기: OV(Organization Validation) 코드 서명 인증서 발급

8. **키 입력 마스킹 기능 (HIGH-02 연계)**  
   - 녹화 시작/중지로 구간 지정, 해당 구간 KeyEvent 마스킹 또는 저장 제외 옵션 UI 제공

9. **경쟁 조건 수정 (LOW-03)**  
   - `get_event_count()`에 `_event_buffer_lock` 적용

---

## 총평

MacroFlow는 팀 내부 배포 도구임을 감안할 때 전반적으로 적절한 보안 의식(경로 검증 시도, ESC×3 인젝션 구분, ctypes argtypes 명시 등)을 갖추고 있다. 그러나 **eval() 샌드박스**는 Python 특성상 `__builtins__: {}` 만으로는 충분하지 않으며, 악의적인 `.json` 또는 `.macroflow` 파일 하나로 RCE가 가능하다는 점이 가장 심각한 문제다. 팀 내 파일 공유 환경에서 사회공학적 공격 벡터로 활용될 수 있으므로 eval 샌드박스 강화를 최우선으로 처리해야 한다.
