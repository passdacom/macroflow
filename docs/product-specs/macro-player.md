# macro-player.md — 재생 기능 스펙

---

## 1. 재생 UX 흐름

```
[재생 실행 전 — 재생 설정 다이얼로그]
  → 속도 배율 선택 (0.5x / 1x / 2x / 5x)
  → 반복 옵션 선택 (1회 / N회 / 무한)
  → 반복 간 딜레이 설정 (ms)
  → "재생 시작" 또는 토글 단축키(F7)

[재생 중]
  → 미니 오버레이 창 표시 (녹화와 동일 위치)
  → 초록 화살표 + 진행률(%) + 속도 배율 표시
  → 단축키로 실시간 제어 가능 (아래 참조)
  → 완료 → 반복 설정에 따라 처리

[긴급 중단]
  → ESC 3회 연속 (500ms 이내) → 즉시 전체 중지
  → 저장 없음, 미니 오버레이 사라짐
```

---

## 2. 재생 전 설정 다이얼로그

재생 단축키(F7) 또는 UI 재생 버튼 클릭 시 표시.

| 설정 항목 | 옵션 | 기본값 |
|---|---|---|
| 속도 배율 | 0.5x / 1x / 2x / 5x (슬라이더 or 드롭다운) | 1x |
| 반복 횟수 | 1회 / N회 입력 / 무한(∞) | 1회 |
| 반복 간 딜레이 | ms 입력 | 500ms |
| 실패 시 기본 동작 | 팝업 / 자동 재시도 / 자동 건너뛰기 / 자동 중지 | 팝업 |

> 마지막 설정값 자동 저장. 다음 재생 시 복원.

---

## 3. 재생 중 단축키 (실시간 제어)

| 단축키 | 동작 | 비고 |
|---|---|---|
| F7 | 재생/일시정지 토글 | |
| ESC × 3회 | 즉시 전체 중지 | 고정 |
| → (오른쪽 화살표) | 다음 이벤트로 즉시 건너뜀 | 느린 구간 빠르게 통과 |
| Space | 일시정지 / 재개 | |
| ↑ / ↓ | 속도 배율 한 단계 올리기/내리기 | 재생 중 실시간 적용 |

> 단축키는 설정에서 변경 가능. 단, ESC 3회는 고정.

---

## 4. 타이밍 재생 엔진

### 핵심 원칙
- `delay_override_ms`가 null인 이벤트: **절대 타임스탬프 기준** 재생
- `delay_override_ms`가 설정된 이벤트: 직전 이벤트 완료 후 해당 ms 대기
- `time.sleep()` 단독 누적 호출 금지 → 드리프트 자동 보정

### 속도 배율 적용
```python
def get_wait_ns(event: MacroEvent, prev_event: MacroEvent | None,
                play_start_ns: int, speed: float) -> int:
    if event.delay_override_ms is not None:
        # delay_override_ms 모드: 직전 이벤트 기준 상대 대기
        return int(event.delay_override_ms * 1_000_000 / speed)
    else:
        # 절대 타임스탬프 모드: 드리프트 보정 포함
        target_ns = play_start_ns + int(event.timestamp_ns / speed)
        return max(0, target_ns - time.perf_counter_ns())
```

### 드리프트 보정
```python
def play_event(event: MacroEvent, wait_ns: int) -> None:
    if wait_ns > 1_000_000:  # 1ms 이상일 때만 sleep
        time.sleep(wait_ns / 1_000_000_000)
    # sleep이 늦게 깨어나도 다음 이벤트의 절대값 계산이 자동 보정
    _execute_event(event)
```

---

## 5. 클릭 / 드래그 판별 (재생 시점)

녹화 데이터에는 mouse_down + mouse_up만 있음. 재생 시 아래 로직으로 판별:

```python
def classify_mouse_action(
    down: MouseDownEvent,
    up: MouseUpEvent,
    settings: MacroSettings,
    screen_w: int,
    screen_h: int
) -> Literal["click", "drag"]:
    dx = (up.x_ratio - down.x_ratio) * screen_w
    dy = (up.y_ratio - down.y_ratio) * screen_h
    dist_px = (dx**2 + dy**2) ** 0.5
    duration_ms = (up.timestamp_ns - down.timestamp_ns) / 1_000_000

    if (dist_px <= settings.click_dist_threshold_px and
            duration_ms <= settings.click_time_threshold_ms):
        return "click"
    return "drag"
```

- click → `send_mouse_click(x, y, button)`
- drag → `send_mouse_drag(down_x, down_y, up_x, up_y)`

---

## 6. color_trigger 재생

```python
def wait_for_color(event: ColorTriggerEvent, hooks: Win32Hooks) -> bool:
    target = hex_to_rgb(event.target_color)
    deadline_ns = time.perf_counter_ns() + event.timeout_ms * 1_000_000
    screen_w, screen_h = get_logical_screen_size()
    x = int(event.x_ratio * screen_w)
    y = int(event.y_ratio * screen_h)

    while time.perf_counter_ns() < deadline_ns:
        actual = hooks.get_pixel_color(x, y)
        if color_matches(actual, target, event.tolerance):
            return True
        time.sleep(event.check_interval_ms / 1000)
    return False  # timeout
```

### timeout 발생 시 처리

재생 설정의 "실패 시 기본 동작"에 따라:

| 설정 | 동작 |
|---|---|
| 팝업 (기본) | 미니 오버레이 일시정지 + 팝업 다이얼로그 표시 |
| 자동 재시도 | 처음 이벤트부터 재시도 (최대 3회, 이후 팝업) |
| 자동 건너뛰기 | 경고 로그 기록 후 다음 이벤트 진행 |
| 자동 중지 | 즉시 재생 중단 |

### 실패 팝업 다이얼로그

```
┌─────────────────────────────────────┐
│  ⚠ color_trigger 대기 시간 초과     │
│                                     │
│  이벤트 #14 (id: d4e5f6a7)          │
│  위치: (25%, 75%)  색: #FFFFFF      │
│  대기 시간: 10초 초과               │
│                                     │
│  [재시도]  [건너뛰기]  [중지]       │
└─────────────────────────────────────┘
```

- 팝업이 뜨는 동안 재생 일시정지 (대상 앱 상태 유지)
- 재시도: 해당 color_trigger 이벤트부터 다시 대기
- 건너뛰기: color_trigger 이후 다음 이벤트부터 진행
- 중지: 전체 재생 중단

---

## 7. 반복 재생

```
반복 횟수: N회 (N = 1 ~ 999, 또는 무한)

[1회차 재생 완료]
  → 반복 간 딜레이 대기
  → 미니 오버레이: "2/5회 재생 중..." 표시
  → 다음 회차 재생 시작

[무한 반복]
  → ESC 3회 또는 F7로 중단할 때까지 계속
  → 미니 오버레이: "∞ 회차 N 재생 중..."

[반복 중 실패]
  → on_timeout 팝업: 재시도/건너뛰기/중지 선택
  → "중지" 선택 시 현재 회차에서 전체 종료
```

---

## 8. 재생 완료 처리

| 상황 | 동작 |
|---|---|
| 단일 재생 완료 | 미니 오버레이 사라짐. 비프음 1회(MB_OK). 아무것도 안 함 |
| N회 반복 완료 | 미니 오버레이 사라짐. 비프음 1회. 완료 토스트 알림 |
| 무한 반복 중단 | 미니 오버레이 사라짐. 중단 비프음(MB_ICONHAND) |
| 오류로 중단 | 미니 오버레이 사라짐. 오류 토스트 알림 + 실패 이벤트 id 표시 |

> 토스트 알림: Windows 10/11 알림 센터 연동 (win32api.Shell_NotifyIcon)
> 소리 피드백은 간단하게 유지. 복잡한 사운드 없이 시스템 비프음만 사용.

---

## 9. 재생 중 "다음 이벤트 건너뜀" 단축키 동작 상세

→ 키 누를 때마다 현재 대기 중인 이벤트를 즉시 실행하고 다음으로 이동.

```
예시: 이벤트 [A(50ms) → B(2000ms) → C(100ms)]
재생 중 B의 2000ms 대기 구간에서 → 키 누름
  → B 즉시 실행
  → C 대기(100ms)로 이동
```

- color_trigger 대기 중에 → 키 누르면: color_trigger 건너뛰고 다음 이벤트로
- mouse_down 실행 후 → 키 누르면: mouse_up도 같이 즉시 실행 (쌍 유지)

---

## 10. 성능 요구사항

| 항목 | 목표값 |
|---|---|
| 타이밍 오차 (단일 이벤트) | < 5ms |
| 누적 드리프트 (이벤트 1000개) | < 10ms |
| CPU 사용률 (재생 중) | < 5% |
| color_trigger 반응 속도 | check_interval_ms 이내 (기본 50ms) |
| 긴급 중단 반응 시간 | < 100ms |
