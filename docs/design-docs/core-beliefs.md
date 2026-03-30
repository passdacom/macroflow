# core-beliefs.md — 설계 원칙 및 과거 실패 학습

> 이 파일은 에이전트가 구현 방향을 결정할 때 참조하는 설계 원칙서입니다.
> "이렇게 해도 되나?" 라는 질문이 생기면 여기서 먼저 답을 찾으세요.
> 원칙을 어기려면 반드시 사용자에게 먼저 확인해야 합니다.

---

## 원칙 1: 녹화는 무손실, 판별은 재생 시점에

### 원칙
녹화 엔진은 발생한 모든 이벤트를 RAW 상태 그대로 저장한다.
클릭인지 드래그인지, 유효한 입력인지 노이즈인지 — 이 판단은 재생 엔진이 한다.

### 왜 이 원칙이 생겼는가
이전 구현에서 녹화 시점에 클릭/드래그를 분류하려 했다.
사람이 클릭할 때 마우스가 미세하게 이동하면 드래그로 분류됐고,
이를 막기 위해 "소폭 이동은 클릭으로 처리" 규칙을 추가했더니
이번엔 실제 드래그가 클릭으로 처리되는 문제가 생겼다.
어느 쪽을 수정해도 다른 쪽이 깨지는 구조적 함정이었다.

### 올바른 구현
```
[녹화] MOUSE_DOWN(x=100, y=200, t=0)
[녹화] MOUSE_MOVE(x=103, y=201, t=15ms)   ← 그대로 저장, 판별하지 않음
[녹화] MOUSE_UP(x=103, y=201, t=87ms)

[재생] 거리=√(3²+1²)=3.16px < CLICK_DIST_THRESHOLD(8px)
       시간=87ms < CLICK_TIME_THRESHOLD(300ms)
       → click(x=100, y=200) 으로 재생   ← 재생 시 판별
```

### 임계값 기본값 및 조정 규칙
- `CLICK_DIST_THRESHOLD`: 기본 8px (매크로별 조정 가능)
- `CLICK_TIME_THRESHOLD`: 기본 300ms (매크로별 조정 가능)
- 이 값들은 JSON 매크로 파일의 `settings` 섹션에 저장

---

## 원칙 2: 이벤트 순서는 OS에 맡긴다

### 원칙
이벤트 캡처는 반드시 단일 스레드 Win32 메시지 펌프에서 처리한다.
Python 레벨에서 이벤트를 멀티스레드로 처리하거나 재정렬하지 않는다.

### 왜 이 원칙이 생겼는가
pynput은 마우스/키보드를 별도 스레드로 처리한다.
빠른 타이핑(예: 100ms 이내 10키 연속 입력) 시 두 스레드의 이벤트가
Python GIL과 스레드 스케줄링 타이밍에 따라 순서가 뒤집힌다.

```
실제 입력: A↓ S↓ A↑ S↑
pynput 기록 가능: A↓ A↑ S↓ S↑  ← 순서 역전
재생 결과: 'a' 하나만 입력된 것처럼 동작
```

### 올바른 구현
```python
# win32/hooks.py
# WH_KEYBOARD_LL + WH_MOUSE_LL 을 같은 메시지 펌프 스레드에서 처리
# 콜백에서는 타임스탬프 찍고 큐에 넣는 것만 함 (최소 처리)
# 직렬화, 필터링, 분류는 별도 소비자 스레드에서 처리

def _ll_hook_callback(nCode, wParam, lParam):
    ts = time.perf_counter_ns()   # 즉시 타임스탬프
    EVENT_QUEUE.append((ts, wParam, lParam))  # deque: lock-free
    return CallNextHookEx(...)    # 체인 유지 필수
```

### 타임스탬프 규칙
- `time.perf_counter_ns()` 사용 (나노초, 단조 증가, 드리프트 없음)
- `time.time()` 또는 `datetime.now()` 사용 금지 (시스템 시계 조정에 취약)

---

## 원칙 3: 타이밍 기준은 절대값, 누적 오차는 보정한다

### 원칙
재생 시 각 이벤트의 실행 시점은 `재생_시작_시각 + 이벤트_타임스탬프` 절대값으로 계산한다.
`time.sleep(delta)` 를 연속 호출하는 방식 사용 금지.

### 왜 이 원칙이 생겼는가
`time.sleep(0.05)` 를 반복 호출하면 OS 스케줄링 오차가 매 호출마다 누적된다.
1000개 이벤트 매크로에서 이벤트당 평균 1ms 오차가 생기면
마지막 이벤트에서는 1초 이상 드리프트가 발생한다.

### 올바른 구현
```python
def play_event(event: MacroEvent, play_start: int, speed: float) -> None:
    target_ns = play_start + int(event.timestamp_ns / speed)
    now_ns = time.perf_counter_ns()
    sleep_ns = target_ns - now_ns
    if sleep_ns > 1_000_000:  # 1ms 이상일 때만 sleep
        time.sleep(sleep_ns / 1_000_000_000)
    # sleep이 늦게 깨어나도 다음 이벤트가 보정함
```

---

## 원칙 4: 좌표는 화면 비율로 정규화한다

### 원칙
JSON에 저장하는 좌표는 픽셀 절대값이 아닌 화면 크기 대비 비율(0.0~1.0)로 저장한다.
재생 시 현재 화면 해상도를 곱해 실제 픽셀 좌표로 변환한다.

### 왜 이 원칙이 생겼는가
녹화 PC와 재생 PC의 해상도가 다르거나 DPI 스케일(125%, 150%)이 다르면
절대 픽셀 좌표로 저장한 매크로가 엉뚱한 위치를 클릭한다.

### 올바른 구현
```python
# 녹화 시 저장
screen_w, screen_h = get_logical_screen_size()  # DPI 보정된 논리 해상도
event.x_ratio = raw_x / screen_w   # 예: 960/1920 = 0.5
event.y_ratio = raw_y / screen_h

# 재생 시 변환
screen_w, screen_h = get_logical_screen_size()
actual_x = int(event.x_ratio * screen_w)
actual_y = int(event.y_ratio * screen_h)
```

### DPI Aware 선언 필수
PyInstaller spec 파일에 반드시 DPI Aware 매니페스트 포함:
```xml
<dpiAware>true/pm</dpiAware>
```
미선언 시 Windows가 앱을 가상 해상도로 실행하여 좌표가 어긋난다.

---

## 원칙 5: 재생은 SendInput, 캡처는 LL Hook

### 원칙
- 재생: `ctypes` 로 `user32.SendInput()` 직접 호출
- 캡처: `ctypes` 로 `user32.SetWindowsHookEx(WH_MOUSE_LL / WH_KEYBOARD_LL)` 직접 호출
- pynput의 재생·캡처 기능은 이 프로젝트에서 사용 금지

### 이유
SendInput은 Windows 입력 큐에 이벤트를 직접 삽입하므로
대상 애플리케이션이 하드웨어 입력과 구분할 수 없다.
pynput의 Controller는 내부적으로 여러 단계를 거쳐 신뢰성이 낮다.

---

## 원칙 6: UI와 엔진은 완전히 분리한다

### 원칙
- `recorder.py`, `player.py`, `macro_file.py` 는 PyQt6를 임포트하지 않는다
- UI는 엔진을 호출하지만, 엔진은 UI를 절대 참조하지 않는다
- 엔진과 UI 간 통신은 Qt Signal/Slot 또는 콜백 함수로만 한다

### 이유
엔진을 UI 독립적으로 유지해야 pytest로 headless 테스트가 가능하다.
UI 없이 CLI에서 매크로를 재생하는 기능 추가도 용이해진다.

---

## 판단이 어려울 때 기준

1. "녹화/재생 품질에 영향을 주는가?" → 원칙 1~5 우선 적용
2. "팀원(비기술자)이 이 동작을 이해할 수 있는가?" → 단순한 쪽 선택
3. "이 선택이 나중에 되돌리기 어려운가?" → 사용자에게 먼저 확인

---

## 원칙 7: 색 감지는 GetPixel, 스크린샷 API 절대 사용 금지

### 원칙
로딩 완료·상태 변화 감지는 Win32 `GetPixel()` 로 단일 픽셀만 읽는다.
`BitBlt`, `PrintWindow`, `CaptureScreen` 등 스크린샷 계열 API 사용 금지.

### 이유
금융사 보안 정책상 화면 캡처가 금지될 수 있다.
GetPixel은 단일 픽셀의 RGB값만 반환하며, 화면 캡처와 무관한 GDI 호출이다.

### 구현 패턴
```python
# win32/hooks.py
def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
    hdc = ctypes.windll.user32.GetDC(0)
    color = ctypes.windll.gdi32.GetPixel(hdc, x, y)
    ctypes.windll.user32.ReleaseDC(0, hdc)
    r = color & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 16) & 0xFF
    return (r, g, b)
```

### tolerance 필수 적용
모니터 색상 프로파일, 밝기 설정에 따라 같은 화면도 RGB가 미세하게 다를 수 있다.
기본 tolerance ±10을 항상 적용한다. 완전 일치(tolerance=0) 사용 금지.

---

## 원칙 8: mouse_move는 녹화 시 무조건 저장, 편집은 UI에서

### 원칙
녹화 엔진은 mouse_move를 필터링하거나 생략하지 않는다.
mouse_move 제거는 사용자가 UI에서 명시적으로 수행한다.

### 이유
녹화 시 mouse_move를 자동으로 버리면 실제 드래그 동작이 손실된다.
사용자가 판단해서 필요 없는 move를 지우는 것이 올바른 워크플로우다.

### UI 워크플로우
1. 녹화 → 전체 이벤트 저장 (mouse_move 포함)
2. 사용자: 녹화 결과 확인
3. 사용자: "mouse_move 일괄 삭제" 버튼 클릭 (원본 .bak 자동 백업)
4. 필요 시 딜레이 개별/일괄 수정
5. 저장
