# MacroFlow Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 즐겨찾기 항목 이름 변경, 파일 덮어쓰기 저장, 텍스트 입력 이벤트, 색 체크 wait 모드, 우클릭 메뉴 단축키 6가지 기능 추가.

**Architecture:**
- `TextInputEvent` 신규 dataclass → `types.py` → `macro_file.py` 직렬화 → `win32/sendinput.py` KEYEVENTF_UNICODE → `player.py` 재생
- `color_check_on_mismatch` Literal 확장: `"skip" | "stop"` → `"skip" | "stop" | "wait"`
- UI 변경은 `editor.py`, `favorites.py`, `main_window.py`에서 독립적으로 처리

**Tech Stack:** Python 3.11+, PyQt6, ctypes Win32 API, pytest 8.x, ruff

---

## 파일 변경 맵

| 파일 | 변경 내용 |
|---|---|
| `src/macroflow/types.py` | `TextInputEvent` 추가, `color_check_on_mismatch` Literal에 `"wait"` 추가 |
| `src/macroflow/macro_file.py` | `text_input` 직렬화/역직렬화, `color_check_on_mismatch` 역직렬화 `"wait"` 지원, `set_color_check_on_mismatch` 시그니처 업데이트 |
| `src/macroflow/win32/sendinput.py` | `KEYEVENTF_UNICODE` 상수, `send_text(text)` 추가 |
| `src/macroflow/win32/mock.py` | `send_text` mock 추가 |
| `src/macroflow/win32/__init__.py` | `send_text` export 추가 |
| `src/macroflow/player.py` | `TextInputEvent` import·재생, 색 체크 `wait` 모드 처리 |
| `src/macroflow/ui/editor.py` | `TextInputEvent` 표시·삽입 UI, wait 색상·토글, 메뉴 accelerator |
| `src/macroflow/ui/favorites.py` | 항목 이름 변경(`_rename_item`) |
| `src/macroflow/ui/main_window.py` | `_save_file()` 덮어쓰기 로직, 툴바 버튼 정리 |
| `tests/test_macro_file.py` | `TextInputEvent` 직렬화 테스트 |
| `tests/test_player.py` | `TextInputEvent` 재생, `wait` 모드 테스트 |

---

## Task 1: types.py — TextInputEvent 추가 + wait Literal

**Files:**
- Modify: `src/macroflow/types.py`

- [ ] **Step 1: `TextInputEvent` dataclass 추가 및 `color_check_on_mismatch` Literal 확장**

`MouseButtonEvent` 정의의 `color_check_on_mismatch` 필드를:
```python
color_check_on_mismatch: Literal["skip", "stop"] = "skip"
```
→
```python
color_check_on_mismatch: Literal["skip", "stop", "wait"] = "skip"
```

`WindowTriggerEvent` 아래, `ConditionEvent` 위에 `TextInputEvent` 추가:
```python
@dataclass(kw_only=True)
class TextInputEvent(MacroEvent):
    """text_input 이벤트 — Unicode 문자열을 KEYEVENTF_UNICODE로 직접 입력.

    키보드 배치·언어 설정과 무관하게 입력한 문자열을 그대로 전송한다.
    한글·영문·숫자·특수문자 모두 지원. IME 우회.

    Attributes:
        text: 입력할 문자열.
    """

    text: str
```

`AnyEvent` union에 `TextInputEvent` 추가:
```python
AnyEvent = (
    MouseButtonEvent
    | MouseMoveEvent
    | MouseWheelEvent
    | KeyEvent
    | WaitEvent
    | ColorTriggerEvent
    | WindowTriggerEvent
    | TextInputEvent
    | ConditionEvent
    | LoopEvent
)
```

- [ ] **Step 2: ruff check 실행**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check src/macroflow/types.py
```

Expected: no errors

- [ ] **Step 3: commit**

```bash
git add src/macroflow/types.py
git commit -m "feat: add TextInputEvent type, extend color_check_on_mismatch to include wait"
```

---

## Task 2: macro_file.py — TextInputEvent 직렬화·역직렬화 + wait 지원

**Files:**
- Modify: `src/macroflow/macro_file.py`
- Test: `tests/test_macro_file.py`

- [ ] **Step 1: test_macro_file.py에 실패 테스트 작성**

`tests/test_macro_file.py` 상단 import에 추가:
```python
from macroflow.types import (
    ...
    TextInputEvent,
)
```

파일 끝에 추가:
```python
# ── TextInputEvent 직렬화 ────────────────────────────────────────────────────

def test_text_input_event_roundtrip(tmp_path: Path) -> None:
    """TextInputEvent가 저장 후 동일하게 로드되어야 한다."""
    events = [
        TextInputEvent(
            id="aa11bb22", type="text_input", timestamp_ns=1_000_000_000,
            text="0031KO01",
        ),
    ]
    macro = MacroData(
        meta=MacroMeta(
            version="1.0", app_version="1.0.0",
            created_at="2026-04-28T00:00:00",
            screen_width=1920, screen_height=1080, dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=copy.deepcopy(events),
        events=events,
    )
    path = str(tmp_path / "text_input.json")
    save(macro, path)
    loaded = load(path)

    assert len(loaded.events) == 1
    ev = loaded.events[0]
    assert isinstance(ev, TextInputEvent)
    assert ev.text == "0031KO01"
    assert ev.type == "text_input"


def test_text_input_korean_roundtrip(tmp_path: Path) -> None:
    """한글 TextInputEvent가 저장 후 동일하게 로드되어야 한다."""
    events = [
        TextInputEvent(
            id="cc33dd44", type="text_input", timestamp_ns=1_000_000_000,
            text="안녕하세요ABC123",
        ),
    ]
    macro = MacroData(
        meta=MacroMeta(
            version="1.0", app_version="1.0.0",
            created_at="2026-04-28T00:00:00",
            screen_width=1920, screen_height=1080, dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=copy.deepcopy(events),
        events=events,
    )
    path = str(tmp_path / "korean.json")
    save(macro, path)
    loaded = load(path)

    ev = loaded.events[0]
    assert isinstance(ev, TextInputEvent)
    assert ev.text == "안녕하세요ABC123"


def test_color_check_wait_roundtrip(tmp_path: Path) -> None:
    """color_check_on_mismatch='wait'가 저장 후 동일하게 로드되어야 한다."""
    events = [
        MouseButtonEvent(
            id="ee55ff66", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#FFFFFF",
            color_check_enabled=True,
            color_check_on_mismatch="wait",
        ),
        MouseButtonEvent(
            id="ff66aa77", type="mouse_up", timestamp_ns=1_100_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
        ),
    ]
    macro = MacroData(
        meta=MacroMeta(
            version="1.0", app_version="1.0.0",
            created_at="2026-04-28T00:00:00",
            screen_width=1920, screen_height=1080, dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=copy.deepcopy(events),
        events=events,
    )
    path = str(tmp_path / "wait.json")
    save(macro, path)
    loaded = load(path)

    ev = loaded.events[0]
    assert isinstance(ev, MouseButtonEvent)
    assert ev.color_check_on_mismatch == "wait"
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
cd /root/.openclaw/workspace/macroflow
python -m pytest tests/test_macro_file.py::test_text_input_event_roundtrip tests/test_macro_file.py::test_text_input_korean_roundtrip tests/test_macro_file.py::test_color_check_wait_roundtrip -v
```

Expected: FAIL (ValueError: Unknown event type 'text_input')

- [ ] **Step 3: macro_file.py 수정**

`_dict_to_event` 함수에서 `mouse_down | mouse_up` case를 수정하여 `"wait"` 지원:
```python
case "mouse_down" | "mouse_up":
    raw_action = d.get("color_check_on_mismatch", "skip")
    on_mismatch: Literal["skip", "stop", "wait"] = (
        "stop" if raw_action == "stop"
        else "wait" if raw_action == "wait"
        else "skip"
    )
    return MouseButtonEvent(
        **common,
        x_ratio=d["x_ratio"],
        y_ratio=d["y_ratio"],
        button=d.get("button", "left"),
        recorded_color=d.get("recorded_color"),
        color_check_enabled=d.get("color_check_enabled", False),
        color_check_on_mismatch=on_mismatch,
    )
```

`window_trigger` case 뒤, `condition` case 앞에 `text_input` case 추가:
```python
case "text_input":
    return TextInputEvent(
        **common,
        text=d.get("text", ""),
    )
```

`_dict_to_event` 함수 상단 import에 `TextInputEvent` 추가:
```python
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)
```

`set_color_check_on_mismatch` 함수 시그니처 업데이트:
```python
def set_color_check_on_mismatch(
    macro: MacroData, event_id: str, action: Literal["skip", "stop", "wait"]
) -> MacroData:
    """events에서 특정 mouse_down 이벤트의 color_check_on_mismatch를 변경한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 mouse_down 이벤트 id.
        action: "skip" — 불일치 시 해당 클릭만 스킵 후 계속 실행.
                "stop" — 불일치 시 재생 전체 즉시 중단.
                "wait" — 픽셀 색이 일치할 때까지 대기 후 클릭 진행.

    Returns:
        color_check_on_mismatch가 변경된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
        TypeError: 해당 이벤트가 MouseButtonEvent가 아닌 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            if not isinstance(event, MouseButtonEvent):
                raise TypeError(f"Event {event_id!r} is not a MouseButtonEvent")
            event.color_check_on_mismatch = action
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd /root/.openclaw/workspace/macroflow
python -m pytest tests/test_macro_file.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: ruff check**

```bash
ruff check src/macroflow/macro_file.py
```

- [ ] **Step 6: commit**

```bash
git add src/macroflow/macro_file.py tests/test_macro_file.py
git commit -m "feat: add TextInputEvent serialization, extend color_check_on_mismatch with wait"
```

---

## Task 3: win32/ — send_text 구현

**Files:**
- Modify: `src/macroflow/win32/sendinput.py`
- Modify: `src/macroflow/win32/mock.py`
- Modify: `src/macroflow/win32/__init__.py`

- [ ] **Step 1: sendinput.py에 KEYEVENTF_UNICODE 상수와 send_text 추가**

기존 상수 블록에 추가:
```python
KEYEVENTF_UNICODE: int = 0x0004
```

`send_key` 함수 아래에 추가:
```python
def send_text(text: str) -> None:
    """Unicode 문자열을 KEYEVENTF_UNICODE로 문자 단위 전송한다.

    키보드 배치·IME 상태에 무관하게 입력한 문자를 그대로 전송한다.
    한글·영문·숫자·특수문자·이모지(서로게이트 쌍) 모두 지원.

    Args:
        text: 입력할 문자열.
    """
    inputs: list[_INPUT] = []
    for ch in text:
        code = ord(ch)
        if code > 0xFFFF:
            # 보충 문자(U+10000 이상): UTF-16 서로게이트 쌍으로 분리
            code -= 0x10000
            high = 0xD800 + (code >> 10)
            low = 0xDC00 + (code & 0x3FF)
            for scan in (high, low):
                inp_down = _INPUT(type=INPUT_KEYBOARD)
                inp_down._input.ki = _KEYBDINPUT(
                    wVk=0, wScan=scan,
                    dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0,
                )
                inp_up = _INPUT(type=INPUT_KEYBOARD)
                inp_up._input.ki = _KEYBDINPUT(
                    wVk=0, wScan=scan,
                    dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0,
                )
                inputs.extend([inp_down, inp_up])
        else:
            inp_down = _INPUT(type=INPUT_KEYBOARD)
            inp_down._input.ki = _KEYBDINPUT(
                wVk=0, wScan=code,
                dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0,
            )
            inp_up = _INPUT(type=INPUT_KEYBOARD)
            inp_up._input.ki = _KEYBDINPUT(
                wVk=0, wScan=code,
                dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0,
            )
            inputs.extend([inp_down, inp_up])

    if inputs:
        _send(*inputs)
```

- [ ] **Step 2: mock.py에 send_text mock 추가**

`send_key` mock 아래에 추가:
```python
def send_text(text: str) -> None:
    logger.debug(f"[Mock] send_text({text!r})")
```

- [ ] **Step 3: `__init__.py`에 send_text export 추가**

Windows 경로 (`from .sendinput import ...`):
```python
from .sendinput import (
    send_key,
    send_mouse_button,
    send_mouse_click,
    send_mouse_drag,
    send_mouse_move,
    send_mouse_wheel,
    send_text,
)
```

비-Windows 경로 (`from .mock import ...`):
```python
from .mock import (
    ...
    send_text,
    ...
)
```

`__all__` 목록에 `"send_text"` 추가:
```python
__all__ = [
    ...
    "send_text",
    ...
]
```

- [ ] **Step 4: ruff check**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check src/macroflow/win32/
```

- [ ] **Step 5: commit**

```bash
git add src/macroflow/win32/sendinput.py src/macroflow/win32/mock.py src/macroflow/win32/__init__.py
git commit -m "feat: add send_text via KEYEVENTF_UNICODE for layout-agnostic text input"
```

---

## Task 4: player.py — TextInputEvent 재생 + wait 색 체크

**Files:**
- Modify: `src/macroflow/player.py`
- Test: `tests/test_player.py`

- [ ] **Step 1: test_player.py에 실패 테스트 작성**

import 블록에 `TextInputEvent`, `MouseButtonEvent` 추가:
```python
from macroflow.types import (
    AnyEvent,
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    TextInputEvent,
    WaitEvent,
)
```

파일 끝에 추가:
```python
# ── TextInputEvent 재생 ──────────────────────────────────────────────────────

class TestTextInputPlayback:
    def test_text_input_calls_send_text(self, mock_win32: object) -> None:
        """TextInputEvent 실행 시 send_text가 호출되어야 한다."""
        from unittest.mock import patch
        event = TextInputEvent(
            id="aa11bb22", type="text_input", timestamp_ns=1_000_000_000,
            text="Hello",
        )
        settings = MacroSettings()
        state = _PlayState()
        with patch("macroflow.player.send_text") as mock_send:
            _execute_event(event, settings, state)
        mock_send.assert_called_once_with("Hello")

    def test_text_input_empty_string(self, mock_win32: object) -> None:
        """빈 문자열 TextInputEvent는 send_text를 호출하지 않아야 한다."""
        from unittest.mock import patch
        event = TextInputEvent(
            id="bb22cc33", type="text_input", timestamp_ns=1_000_000_000,
            text="",
        )
        settings = MacroSettings()
        state = _PlayState()
        with patch("macroflow.player.send_text") as mock_send:
            _execute_event(event, settings, state)
        mock_send.assert_not_called()


# ── 색 체크 wait 모드 ────────────────────────────────────────────────────────

class TestColorCheckWait:
    def test_wait_mode_polls_until_match(self, mock_win32: object) -> None:
        """wait 모드: 픽셀 색이 일치할 때까지 폴링 후 클릭이 진행되어야 한다."""
        from unittest.mock import patch, call
        import macroflow.win32 as w32

        down = MouseButtonEvent(
            id="cc33dd44", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
            recorded_color="#FF0000",
            color_check_enabled=True,
            color_check_on_mismatch="wait",
        )
        settings = MacroSettings(color_check_click_tolerance=10)
        state = _PlayState()

        call_count = 0
        def side_effect(x: int, y: int) -> tuple[int, int, int]:
            nonlocal call_count
            call_count += 1
            # 처음 두 번은 불일치, 세 번째부터 일치
            if call_count < 3:
                return (0, 0, 0)
            return (255, 0, 0)  # #FF0000

        with patch.object(w32, "get_pixel_color", side_effect=side_effect), \
             patch.object(w32, "send_mouse_move"), \
             patch.object(w32, "send_mouse_button") as mock_button:
            _execute_event(down, settings, state)

        # 픽셀이 일치한 후 클릭이 실행되어야 함
        assert mock_button.called
        assert call_count >= 3
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
cd /root/.openclaw/workspace/macroflow
python -m pytest tests/test_player.py::TestTextInputPlayback tests/test_player.py::TestColorCheckWait -v
```

Expected: FAIL

- [ ] **Step 3: player.py 수정 — TextInputEvent import 및 재생**

import 블록에 `TextInputEvent`, `send_text` 추가:
```python
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)
from macroflow.win32 import (
    find_window,
    get_pixel_color,
    ratio_to_pixel,
    send_key,
    send_mouse_button,
    send_mouse_drag,
    send_mouse_move,
    send_mouse_wheel,
    send_text,
)
```

`_execute_event` 함수 내 `elif isinstance(event, WaitEvent):` 블록 앞에 추가:
```python
    elif isinstance(event, TextInputEvent):
        if event.text:
            send_text(event.text)
```

- [ ] **Step 4: player.py 수정 — wait 색 체크 모드**

`_execute_event` 내 `mouse_down` 색 체크 블록을:
```python
if event.color_check_enabled and event.recorded_color is not None:
    send_mouse_move(x, y)
    time.sleep(0.05)
    actual = get_pixel_color(x, y)
    target = _hex_to_rgb(event.recorded_color)
    if not _color_matches(actual, target, settings.color_check_click_tolerance):
        actual_hex = f"#{actual[0]:02X}{actual[1]:02X}{actual[2]:02X}"
        if event.color_check_on_mismatch == "stop":
            raise PlaybackError(
                f"색 체크 불일치 → 재생 중단 "
                f"at ({x},{y}) 실제={actual_hex} 기록={event.recorded_color}"
            )
        state.color_check_skip_button = event.button
        logger.debug(
            f"[color_check] skip click at ({x},{y}): "
            f"actual={actual_hex} target={event.recorded_color}"
        )
        return
```

다음으로 교체:
```python
if event.color_check_enabled and event.recorded_color is not None:
    send_mouse_move(x, y)
    time.sleep(0.05)  # hover 효과 대기
    target = _hex_to_rgb(event.recorded_color)

    if event.color_check_on_mismatch == "wait":
        # wait 모드: 색이 일치할 때까지 폴링 (타임아웃 시 skip)
        _wait_for_color_check(x, y, target, settings)
        # 폴링 후 실제 클릭은 아래에서 계속 진행
    else:
        actual = get_pixel_color(x, y)
        if not _color_matches(actual, target, settings.color_check_click_tolerance):
            actual_hex = f"#{actual[0]:02X}{actual[1]:02X}{actual[2]:02X}"
            if event.color_check_on_mismatch == "stop":
                raise PlaybackError(
                    f"색 체크 불일치 → 재생 중단 "
                    f"at ({x},{y}) 실제={actual_hex} 기록={event.recorded_color}"
                )
            # skip 모드: 이 클릭 스킵, 대응하는 up도 스킵하도록 표시
            state.color_check_skip_button = event.button
            logger.debug(
                f"[color_check] skip click at ({x},{y}): "
                f"actual={actual_hex} target={event.recorded_color}"
            )
            return
```

`_hex_to_rgb` 함수 앞에 `_wait_for_color_check` 헬퍼 추가:
```python
def _wait_for_color_check(
    x: int, y: int,
    target: tuple[int, int, int],
    settings: MacroSettings,
) -> None:
    """색 체크 wait 모드: 지정 픽셀 색이 일치할 때까지 폴링한다.

    타임아웃 시 경고 로그만 남기고 클릭을 계속 진행한다 (skip과 달리 클릭은 실행).

    Args:
        x: 검사할 픽셀 X 좌표.
        y: 검사할 픽셀 Y 좌표.
        target: 기다릴 목표 RGB 색.
        settings: color_trigger_check_interval_ms, color_trigger_default_timeout_ms 사용.
    """
    deadline_ns = (
        time.perf_counter_ns()
        + settings.color_trigger_default_timeout_ms * 1_000_000
    )
    interval_s = settings.color_trigger_check_interval_ms / 1000.0

    while time.perf_counter_ns() < deadline_ns:
        if _stop_flag.is_set():
            return
        actual = get_pixel_color(x, y)
        if _color_matches(actual, target, settings.color_check_click_tolerance):
            return
        time.sleep(interval_s)

    logger.warning(
        f"[color_check wait] timeout at ({x},{y}), proceeding with click anyway"
    )
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd /root/.openclaw/workspace/macroflow
python -m pytest tests/test_player.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 6: ruff check**

```bash
ruff check src/macroflow/player.py
```

- [ ] **Step 7: commit**

```bash
git add src/macroflow/player.py tests/test_player.py
git commit -m "feat: add TextInputEvent playback and color check wait mode"
```

---

## Task 5: editor.py — TextInputEvent UI + wait 색상·토글 + accelerator

**Files:**
- Modify: `src/macroflow/ui/editor.py`

- [ ] **Step 1: import에 TextInputEvent 추가**

`editor.py`의 `from macroflow.types import (...)` 블록에 `TextInputEvent` 추가:
```python
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)
```

- [ ] **Step 2: `_KIND_COLORS`에 신규 색상 추가**

기존 딕셔너리에 추가 (기존 항목들 사이에):
```python
    # wait 색상 (파란 계열)
    "color_check_click_wait":       QColor(40,  120, 210),  # 파랑 — 색 체크 대기 모드
    "color_check_right_click_wait": QColor(30,   90, 180),  # 진한 파랑
    # 텍스트 입력
    "text_input":                   QColor(0,   170, 130),  # 녹청(teal)
```

- [ ] **Step 3: `_DisplayRow`에 `color_check_on_mismatch` 기본값 업데이트**

`_DisplayRow` dataclass의 `color_check_on_mismatch` 필드 타입을:
```python
color_check_on_mismatch: str = "skip"     # "skip" | "stop"
```
→
```python
color_check_on_mismatch: str = "skip"     # "skip" | "stop" | "wait"
```
(타입 주석만 변경, 기능 변경 없음)

- [ ] **Step 4: `_build_rows`에 TextInputEvent 행 처리 및 wait 색상 추가**

기존 `_build_rows` 함수에서 마우스 버튼 down 처리 블록의 `is_color_check` 분기를 교체:

기존:
```python
elif is_color_check:
    is_stop = event.color_check_on_mismatch == "stop"
    emoji = "🛑" if is_stop else "🎨"
    if event.button == "left":
        kind = "color_check_click_stop" if is_stop else "color_check_click"
    else:
        kind = ("color_check_right_click_stop" if is_stop
                else "color_check_right_click")
    label = f"클릭({btn_ko}) {emoji}"
```

교체:
```python
elif is_color_check:
    mismatch = event.color_check_on_mismatch
    is_stop = mismatch == "stop"
    is_wait = mismatch == "wait"
    emoji = "🛑" if is_stop else ("⏳" if is_wait else "🎨")
    if event.button == "left":
        if is_stop:
            kind = "color_check_click_stop"
        elif is_wait:
            kind = "color_check_click_wait"
        else:
            kind = "color_check_click"
    else:
        if is_stop:
            kind = "color_check_right_click_stop"
        elif is_wait:
            kind = "color_check_right_click_wait"
        else:
            kind = "color_check_right_click"
    label = f"클릭({btn_ko}) {emoji}"
```

그리고 `_build_rows` 끝 부분 (WaitEvent, ColorTriggerEvent 등 처리 블록 뒤)에 `TextInputEvent` 처리 추가:
```python
        # ── 텍스트 입력 ──────────────────────────────────────────────────────
        elif isinstance(event, TextInputEvent):
            consumed.add(i)
            preview = event.text if len(event.text) <= 30 else event.text[:27] + "..."
            rows.append(_DisplayRow(
                "text_input", "텍스트 입력", f'"{preview}"',
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))
```

`WaitEvent` 처리 블록 앞에 위치하도록 삽입. 기존 WaitEvent 블록 패턴을 참고:

```python
        # ── 대기 ─────────────────────────────────────────────────────────────
        elif isinstance(event, WaitEvent):
```

위 블록 바로 앞에 TextInputEvent 블록을 배치한다.

- [ ] **Step 5: `_COLOR_CHECK_KINDS` 상수 업데이트**

`_context_menu` 내부의 `_COLOR_CHECK_KINDS` 튜플에 wait 변종 추가:
```python
_COLOR_CHECK_KINDS = (
    "click", "right_click", "drag", "right_drag",
    "color_check_click", "color_check_right_click",
    "color_check_click_stop", "color_check_right_click_stop",
    "color_check_click_wait", "color_check_right_click_wait",
)
```

그리고 `_on_double_click` 내부의 동일 패턴도 동일하게 업데이트:
```python
            elif display_row.kind in (
                "click", "right_click", "drag", "right_drag",
                "color_check_click", "color_check_right_click",
                "color_check_click_stop", "color_check_right_click_stop",
                "color_check_click_wait", "color_check_right_click_wait",
                "orphan", "mouse_move",
            ):
```

- [ ] **Step 6: 컨텍스트 메뉴 — 텍스트 입력 추가 액션 + accelerator**

`_context_menu` 함수의 `len(rows) == 1` 블록에서:
1. `act_edit_delay`에 accelerator 추가
2. 색 체크 모드 토글 메뉴 텍스트에 wait 표시
3. 텍스트 입력 추가 액션 삽입

전체 `len(rows) == 1` 블록 교체 (기존 메뉴 항목들에 accelerator `(&X)` 추가):
```python
        if len(rows) == 1:
            row = self._rows[rows[0]]
            primary = self._macro.events[row.primary_idx]

            # ▶ 이 이벤트만 실행
            act_play_single = menu.addAction("▶ 이 이벤트만 실행")
            assert act_play_single is not None
            act_play_single.triggered.connect(lambda: self._play_single_event(rows[0]))
            menu.addSeparator()

            act_edit_delay = menu.addAction("딜레이 설정(&D)...")
            assert act_edit_delay is not None
            act_edit_delay.triggered.connect(lambda: self._edit_delay(rows[0]))

            if row.kind == "key_press" and isinstance(primary, KeyEvent):
                act_edit_key = menu.addAction("키 값 변경(&K)...")
                assert act_edit_key is not None
                act_edit_key.triggered.connect(lambda: self._edit_key(rows[0]))

            _COLOR_CHECK_KINDS = (
                "click", "right_click", "drag", "right_drag",
                "color_check_click", "color_check_right_click",
                "color_check_click_stop", "color_check_right_click_stop",
                "color_check_click_wait", "color_check_right_click_wait",
            )

            if row.kind in _COLOR_CHECK_KINDS + ("orphan", "mouse_move"):
                act_edit_pos = menu.addAction("위치 변경(&P)...")
                assert act_edit_pos is not None
                act_edit_pos.triggered.connect(lambda: self._edit_position(rows[0]))

            # 색 체크 토글 — recorded_color가 있는 클릭/드래그에서만 표시
            if row.kind in _COLOR_CHECK_KINDS and isinstance(primary, MouseButtonEvent) and primary.recorded_color is not None:
                is_checked = primary.color_check_enabled
                check_text = "🎨 색 체크 끄기(&C)" if is_checked else "🎨 색 체크 켜기(&C)"
                act_color = menu.addAction(check_text)
                assert act_color is not None
                act_color.triggered.connect(lambda: self._toggle_color_check(rows[0]))

                # 불일치 동작 전환 (색 체크 활성화된 경우만) — skip→stop→wait 순환
                if is_checked:
                    mismatch = primary.color_check_on_mismatch
                    if mismatch == "skip":
                        mode_text = "⏹ 불일치 시: 중지로 변경(&M)"
                    elif mismatch == "stop":
                        mode_text = "⏳ 불일치 시: 대기로 변경(&M)"
                    else:  # wait
                        mode_text = "▶ 불일치 시: 스킵으로 변경(&M)"
                    act_mode = menu.addAction(mode_text)
                    assert act_mode is not None
                    act_mode.triggered.connect(
                        lambda: self._toggle_color_check_mode(rows[0])
                    )

            if row.kind == "mouse_wheel":
                act_edit_wheel = menu.addAction("스크롤 편집(&W)...")
                assert act_edit_wheel is not None
                act_edit_wheel.triggered.connect(lambda: self._edit_wheel(rows[0]))

            if row.kind == "text_input" and isinstance(primary, TextInputEvent):
                act_edit_text = menu.addAction("💬 텍스트 편집(&E)...")
                assert act_edit_text is not None
                act_edit_text.triggered.connect(lambda: self._edit_text_input(rows[0]))

            act_text_insert = menu.addAction("💬 텍스트 입력 추가(&T)...")
            assert act_text_insert is not None
            act_text_insert.triggered.connect(lambda: self._insert_text_input(rows[0]))

            act_remark = menu.addAction("📝 비고 편집(&N)...")
            assert act_remark is not None
            act_remark.triggered.connect(lambda: self._edit_remark(rows[0]))

            menu.addSeparator()

        act_delete = menu.addAction(f"행 삭제(&X) ({len(rows)}개)")
        assert act_delete is not None
        act_delete.triggered.connect(lambda: self._delete_rows(rows))
```

- [ ] **Step 7: `_toggle_color_check_mode` — 3-way 순환으로 수정**

기존 `_toggle_color_check_mode` 메서드를 교체:
```python
    def _toggle_color_check_mode(self, row_idx: int) -> None:
        """지정 행 클릭 이벤트의 color_check_on_mismatch를 skip → stop → wait → skip 순환으로 전환한다."""
        from typing import Literal
        if self._macro is None or row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        primary = self._macro.events[row.primary_idx]
        if not isinstance(primary, MouseButtonEvent) or not primary.color_check_enabled:
            return
        _cycle: dict[str, Literal["skip", "stop", "wait"]] = {
            "skip": "stop", "stop": "wait", "wait": "skip",
        }
        new_mode: Literal["skip", "stop", "wait"] = _cycle.get(
            primary.color_check_on_mismatch, "skip"
        )
        self._push_undo()
        try:
            new_macro = set_color_check_on_mismatch(self._macro, primary.id, new_mode)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            return
        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)
```

- [ ] **Step 8: `_insert_text_input` 메서드 추가**

`_toggle_color_check_mode` 아래에 추가:
```python
    def _insert_text_input(self, row_idx: int) -> None:
        """선택 행 다음에 TextInputEvent를 삽입한다.

        QInputDialog로 입력할 텍스트를 받아 이벤트 목록에 삽입.
        타임스탬프는 직전 이벤트 + 1초. 이후 이벤트는 1초 시프트.
        """
        if self._macro is None:
            return

        text, ok = QInputDialog.getText(
            self, "텍스트 입력 추가",
            "입력할 텍스트를 입력하세요:\n"
            "(한글·영문·숫자·특수문자 모두 지원. 키보드 배치 무관.)",
        )
        if not ok or not text:
            return

        rows = self._selected_row_indices()
        if rows:
            last_row = self._rows[rows[-1]]
            insert_after_event_idx = max(last_row.event_indices)
        else:
            insert_after_event_idx = len(self._macro.events) - 1

        _BUDGET_NS = 1_000_000_000  # 1초

        evs = self._macro.events
        if 0 <= insert_after_event_idx < len(evs):
            prev_ts_ns = evs[insert_after_event_idx].timestamp_ns
        elif evs:
            prev_ts_ns = evs[-1].timestamp_ns
        else:
            prev_ts_ns = 0

        new_event = TextInputEvent(
            id=secrets.token_hex(4),
            type="text_input",
            timestamp_ns=prev_ts_ns + _BUDGET_NS,
            delay_override_ms=None,
            text=text,
        )
        self._push_undo()
        events = list(self._macro.events)
        events.insert(insert_after_event_idx + 1, new_event)

        # 삽입 지점 이후 이벤트 1초 시프트 → 타이밍 보존
        for i in range(insert_after_event_idx + 2, len(events)):
            ev = events[i]
            events[i] = dataclasses.replace(ev, timestamp_ns=ev.timestamp_ns + _BUDGET_NS)

        self._apply_events(events)

    def _edit_text_input(self, row_idx: int) -> None:
        """TextInputEvent의 텍스트를 수정한다."""
        if self._macro is None or row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        primary = self._macro.events[row.primary_idx]
        if not isinstance(primary, TextInputEvent):
            return

        text, ok = QInputDialog.getText(
            self, "텍스트 편집",
            "입력할 텍스트를 수정하세요:",
            text=primary.text,
        )
        if not ok:
            return

        self._push_undo()
        updated = copy.deepcopy(self._macro.events)
        for i, ev in enumerate(updated):
            if ev.id == primary.id and isinstance(ev, TextInputEvent):
                updated[i] = dataclasses.replace(ev, text=text)
                break
        self._apply_events(updated)
```

더블클릭(`_on_double_click`) 내 `text_input` 처리 추가. 기존 `else:` 분기 전에 추가:
```python
            elif display_row.kind == "text_input":
                self._edit_text_input(row)
```

- [ ] **Step 9: ruff check**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check src/macroflow/ui/editor.py
```

Expected: no errors. 오류가 있으면 수정 후 재실행.

- [ ] **Step 10: commit**

```bash
git add src/macroflow/ui/editor.py
git commit -m "feat: add TextInputEvent editor UI, color check wait mode display/toggle, menu accelerators"
```

---

## Task 6: favorites.py — 항목 이름 변경

**Files:**
- Modify: `src/macroflow/ui/favorites.py`

- [ ] **Step 1: `_rename_item` 메서드 추가**

`_remove_item` 메서드 바로 앞에 추가:
```python
    def _rename_item(self, item: QTreeWidgetItem) -> None:
        """즐겨찾기 항목의 이름을 변경하고 실제 파일도 rename한다.

        인덱스의 filename과 파일 경로를 동시에 업데이트한다.
        """
        if self._favorites_dir is None:
            return
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        old_path = Path(data.get("path", ""))
        if not old_path.exists():
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{old_path}")
            self._refresh_tree()
            return

        old_stem = old_path.stem
        new_stem, ok = QInputDialog.getText(
            self, "이름 변경", "새 이름:", text=old_stem
        )
        if not ok or not new_stem.strip():
            return

        safe_name = _sanitize_filename(new_stem.strip())
        if not safe_name:
            QMessageBox.warning(self, "오류", "사용할 수 없는 이름입니다.")
            return

        new_path = self._favorites_dir / f"{safe_name}.json"
        if new_path.exists() and new_path != old_path:
            QMessageBox.warning(
                self, "중복 이름",
                f"이미 같은 이름의 파일이 있습니다:\n{new_path.name}"
            )
            return

        try:
            old_path.rename(new_path)
        except OSError as e:
            QMessageBox.warning(self, "이름 변경 오류", str(e))
            return

        # 인덱스 업데이트
        old_filename = old_path.name
        new_filename = new_path.name
        for g in self._index.get("groups", []):
            items: list[str] = g.get("items", [])
            if old_filename in items:
                idx = items.index(old_filename)
                items[idx] = new_filename
                break

        self._save_index()
        self._refresh_tree()
        logger.info(f"즐겨찾기 이름 변경: {old_filename} → {new_filename}")
```

- [ ] **Step 2: `_build_item_menu`에 이름 변경 액션 추가**

기존 `_build_item_menu` 메서드에서 `act_open` 액션 뒤, `act_seq` 앞 위치에 추가:

```python
    def _build_item_menu(self, menu: QMenu, item: QTreeWidgetItem) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        path: str = data.get("path", "")
        filename = Path(path).name if path else ""
        current_gid = self._find_item_group_id(filename)

        act_open = menu.addAction("📂 에디터로 열기")
        assert act_open is not None
        act_open.triggered.connect(lambda: self._open_item(item))

        act_seq = menu.addAction("📋 시퀀서에 추가")
        assert act_seq is not None
        act_seq.triggered.connect(lambda: self._add_item_to_sequencer(item))

        menu.addSeparator()

        act_rename = menu.addAction("✏️ 이름 변경")
        assert act_rename is not None
        act_rename.triggered.connect(lambda: self._rename_item(item))

        menu.addSeparator()

        # 그룹 이동 서브메뉴
        move_menu = menu.addMenu("📁 그룹으로 이동")
        assert move_menu is not None
        has_target = False
        for g in self._index.get("groups", []):
            gid: str = g.get("id", "")
            if gid == current_gid:
                continue
            gname: str = g.get("name", "그룹")
            act_move = move_menu.addAction(f"📁 {gname}")
            assert act_move is not None
            act_move.triggered.connect(
                lambda _checked=False, _fn=filename, _gid=gid:
                    self._move_item_to_group(_fn, _gid)
            )
            has_target = True
        if not has_target:
            no_target = move_menu.addAction("(이동 가능한 그룹 없음)")
            assert no_target is not None
            no_target.setEnabled(False)

        menu.addSeparator()

        act_remove = menu.addAction("🗑 즐겨찾기에서 제거")
        assert act_remove is not None
        act_remove.triggered.connect(lambda: self._remove_item(item))
```

- [ ] **Step 3: ruff check**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check src/macroflow/ui/favorites.py
```

- [ ] **Step 4: commit**

```bash
git add src/macroflow/ui/favorites.py
git commit -m "feat: add rename item in favorites with actual file rename"
```

---

## Task 7: main_window.py — 파일 저장 덮어쓰기 + 툴바 정리

**Files:**
- Modify: `src/macroflow/ui/main_window.py`

- [ ] **Step 1: `_save_file` 메서드 수정 — 덮어쓰기 로직**

기존:
```python
    def _save_file(self) -> None:
        """항상 '다른 이름으로 저장' 다이얼로그를 열어 저장 경로를 지정한다."""
        self._save_file_as()
```

교체:
```python
    def _save_file(self) -> None:
        """현재 파일에 덮어쓰기 저장한다.

        _current_file이 설정된 경우: 확인 다이얼로그 후 덮어쓰기.
        _current_file이 없는 경우: _save_file_as()로 위임.
        """
        if not self._macro:
            return
        if self._current_file is None:
            self._save_file_as()
            return
        reply = QMessageBox.question(
            self,
            "덮어쓰기 저장",
            f"현재 파일에 덮어씁니다:\n\n{self._current_file}\n\n계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._do_save(str(self._current_file))
```

- [ ] **Step 2: 툴바 버튼 정리 — "저장"과 "다른 이름으로 저장" 분리**

`_setup_toolbar` 내 3행 툴바(`tb3`) 구성에서:

기존:
```python
        self._act_save = QAction("💾 다른 이름으로 저장", self)
        self._act_save.triggered.connect(self._save_file)
        tb3.addAction(self._act_save)
```

교체:
```python
        self._act_save = QAction("💾 저장  Ctrl+S", self)
        self._act_save.setToolTip("현재 파일에 덮어쓰기 저장 (파일이 없으면 다른 이름으로 저장)")
        self._act_save.triggered.connect(self._save_file)
        tb3.addAction(self._act_save)

        self._act_save_as = QAction("💾 다른 이름으로 저장", self)
        self._act_save_as.setToolTip("새 경로를 지정하여 저장")
        self._act_save_as.triggered.connect(self._save_file_as)
        tb3.addAction(self._act_save_as)
```

- [ ] **Step 3: ruff check**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check src/macroflow/ui/main_window.py
```

- [ ] **Step 4: 전체 테스트 실행**

```bash
cd /root/.openclaw/workspace/macroflow
python -m pytest tests/ -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: commit**

```bash
git add src/macroflow/ui/main_window.py
git commit -m "feat: file save overwrites current file with confirmation, add separate save-as toolbar button"
```

---

## 최종 검증

- [ ] **전체 ruff check**

```bash
cd /root/.openclaw/workspace/macroflow
ruff check src/
```

Expected: no errors

- [ ] **전체 테스트**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: 모든 테스트 PASS

- [ ] **dev-log 업데이트** (`docs/dev-log.md` 최상단에 추가)

```markdown
## v1.1.0 — 2026-04-28

### 신규 기능 6종

#### ① 텍스트 입력 이벤트 (`types.py`, `macro_file.py`, `win32/sendinput.py`, `player.py`, `editor.py`)
- **새 이벤트 타입**: `TextInputEvent(text: str)` — `KEYEVENTF_UNICODE`로 문자 단위 전송
- 키보드 배치·IME·언어 설정 무관. 한글·영문·숫자·특수문자 모두 지원.
- 에디터 우클릭 → "💬 텍스트 입력 추가" → 선택 행 다음에 삽입
- 에디터 표시: 녹청(teal)색, 내용 열에 텍스트 미리보기

#### ② 색 체크 wait 모드 (`types.py`, `macro_file.py`, `player.py`, `editor.py`)
- `color_check_on_mismatch` 3번째 옵션 추가: `"wait"`
- 재생 시: 지정 픽셀 색이 일치할 때까지 폴링 → 일치 후 클릭 진행 (타임아웃 시 경고 후 클릭)
- 에디터 표시: 파란색 계열 (`⏳` 이모지)
- 우클릭 모드 전환: skip(🎨) → stop(🛑) → wait(⏳) → skip 3-way 순환

#### ③ 우클릭 메뉴 단축키 (`editor.py`)
- 메뉴 항목에 `(&X)` accelerator 추가
- D=딜레이 설정, K=키 값 변경, P=위치 변경, C=색 체크 켜기/끄기, M=모드 변경, W=스크롤 편집, E=텍스트 편집, T=텍스트 입력 추가, N=비고 편집, X=행 삭제

#### ④ 즐겨찾기 항목 이름 변경 (`favorites.py`)
- 즐겨찾기 항목 우클릭 → "✏️ 이름 변경"
- 실제 파일 rename + `_index.json` 업데이트 동시 처리
- 중복 이름 감지, 파일 오류 시 롤백 없음 경고

#### ⑤ 파일 저장 덮어쓰기 (`main_window.py`)
- Ctrl+S / "💾 저장" → 현재 파일에 덮어쓰기 (확인 다이얼로그 포함)
- 저장 경로 없으면 자동으로 다른 이름으로 저장 다이얼로그 열림
- 툴바에 "다른 이름으로 저장" 버튼 별도 추가

#### ⑥ 시퀀서 병합 간격 (확인)
- `_gap_spin.value()` → `merge_macros(gap_ms=...)` 정상 전달 확인. 수정 불필요.
```

- [ ] **최종 commit**

```bash
git add docs/dev-log.md
git commit -m "docs: update dev-log for v1.1.0 features"
```
