# json-format-spec.md — 매크로 JSON 포맷 명세

> ★ 이 파일은 모든 모듈의 데이터 계약입니다.
> recorder.py / player.py / script_engine.py / ui/ 전부 이 스펙을 따릅니다.
> 포맷 변경 시 이 파일을 먼저 수정하고, 이후 구현을 변경하세요.

---

## 1. 파일 최상위 구조

```json
{
  "meta": { ... },
  "settings": { ... },
  "raw_events": [ ... ],
  "events": [ ... ],
  "is_edited": false
}
```

| 필드 | 설명 |
|---|---|
| meta | 파일 메타데이터 |
| settings | 재생·판별 임계값 |
| raw_events | 녹화 원본. 저장 후 절대 수정하지 않음 |
| events | 실제 재생에 사용하는 편집본. 모든 편집은 여기서만 |
| is_edited | raw_events와 events가 다른지 여부 |

### raw_events / events 관계 규칙

```
[녹화 완료 직후]
raw_events = events = 전체 이벤트 (동일한 내용)
is_edited = false

[mouse_move 일괄 삭제]
raw_events → 변경 없음 (절대 건드리지 않음)
events     → mouse_move 항목 제거
is_edited  → true

[딜레이 수정]
raw_events → 변경 없음
events     → 해당 이벤트의 delay_override_ms 수정
is_edited  → true

["원본으로 되돌리기" 실행]
events     → raw_events 전체 복사
is_edited  → false
```

> **재생 엔진(player.py)은 events만 읽는다. raw_events는 절대 참조하지 않는다.**

---

## 2. meta 섹션

```json
"meta": {
  "version": "1.0",
  "app_version": "0.1.0",
  "created_at": "2025-01-15T14:30:00",
  "author": "",
  "description": "",
  "screen_width": 1920,
  "screen_height": 1080,
  "dpi_scale": 1.25
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| version | string | JSON 스키마 버전. 마이그레이션 판단에 사용 |
| screen_width / height | int | 녹화 당시 논리 해상도 (DPI 보정 후) |
| dpi_scale | float | 녹화 PC의 DPI 배율 (1.0=100%, 1.25=125%) |

---

## 3. settings 섹션

```json
"settings": {
  "click_dist_threshold_px": 8,
  "click_time_threshold_ms": 300,
  "default_playback_speed": 1.0,
  "color_trigger_check_interval_ms": 50,
  "color_trigger_default_timeout_ms": 10000
}
```

| 필드 | 기본값 | 설명 |
|---|---|---|
| click_dist_threshold_px | 8 | 클릭 판별 거리 임계값 |
| click_time_threshold_ms | 300 | 클릭 판별 시간 임계값 |
| default_playback_speed | 1.0 | 재생 속도 배율 (0.5 ~ 10.0) |
| color_trigger_check_interval_ms | 50 | 색 감지 폴링 주기 |
| color_trigger_default_timeout_ms | 10000 | 색 감지 최대 대기 시간 |

---

## 4. 이벤트 공통 필드

모든 이벤트는 아래 공통 필드를 가진다:

```json
{
  "id": "a1b2c3d4",
  "type": "이벤트_타입",
  "timestamp_ns": 1234567890,
  "delay_override_ms": null
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| id | string | 8자리 hex UUID. 녹화 시 생성, 이후 변경 불가. index 대신 이 값으로 이벤트를 식별 |
| type | string | 이벤트 종류 |
| timestamp_ns | int | 녹화 시작 기준 경과 나노초 (perf_counter_ns). raw_events에서 절대 변경 안 함 |
| delay_override_ms | int \| null | null이면 timestamp_ns 기준 절대시간 재생. 값이 있으면 직전 이벤트 후 N ms 대기 |

### id 생성 규칙
```python
import secrets
event_id = secrets.token_hex(4)  # 예: "a1b2c3d4"
```
- 녹화 시점에 생성
- raw_events와 events가 동일한 id를 공유 (복사 시 id 유지)
- UI에서 이벤트를 식별/참조할 때 index 대신 id 사용

### delay_override_ms 동작 규칙
```
null  → timestamp_ns 기준 절대 시간으로 재생 (원래 타이밍)
0     → 직전 이벤트 직후 즉시 실행
200   → 직전 이벤트 실행 후 200ms 대기
```

- UI "딜레이 개별 수정": 선택한 이벤트 id의 delay_override_ms 설정
- UI "딜레이 일괄 수정": events 전체의 delay_override_ms를 동일값으로 설정
- 일괄 설정 후 특정 이벤트 개별 수정 가능 (일괄값을 덮어씀)
- delay_override_ms를 null로 되돌리면 원래 타이밍 복원

---

## 5. 이벤트 타입 상세

### 5-1. mouse_down / mouse_up

```json
{
  "id": "a1b2c3d4",
  "type": "mouse_down",
  "timestamp_ns": 1000000000,
  "delay_override_ms": null,
  "x_ratio": 0.5,
  "y_ratio": 0.3,
  "button": "left"
}
```

| 필드 | 타입 | 값 |
|---|---|---|
| x_ratio | float | 0.0~1.0. 화면 너비 대비 비율 |
| y_ratio | float | 0.0~1.0. 화면 높이 대비 비율 |
| button | string | "left" \| "right" \| "middle" |

> mouse_down + mouse_up은 항상 쌍으로 저장된다.
> 재생 시 click/drag 판별은 player.py가 settings 임계값으로 수행한다.
> **녹화 엔진은 절대 판별하지 않는다.** (core-beliefs.md 원칙 1)

---

### 5-2. mouse_move

```json
{
  "id": "b2c3d4e5",
  "type": "mouse_move",
  "timestamp_ns": 1010000000,
  "delay_override_ms": null,
  "x_ratio": 0.501,
  "y_ratio": 0.300
}
```

> UI "mouse_move 일괄 삭제": events에서 type=="mouse_move"인 항목 전부 제거.
> raw_events는 그대로 보존.
> mouse_move가 없으면 player.py는 클릭/키 사이에 마우스를 이동시키지 않는다.

---

### 5-3. key_down / key_up

```json
{
  "id": "c3d4e5f6",
  "type": "key_down",
  "timestamp_ns": 2000000000,
  "delay_override_ms": null,
  "key": "a",
  "vk_code": 65
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| key | string | 사람이 읽을 수 있는 키 이름 (예: "a", "enter", "ctrl", "f1") |
| vk_code | int | Windows Virtual Key Code. 재생 시 이 값 사용 |

> key_down + key_up 쌍이 항상 함께 저장된다.
> Win32 LL Hook 단일 메시지 펌프가 빠른 타이핑에서도 순서를 보장한다.

---

### 5-4. wait

```json
{
  "id": "d4e5f6a7",
  "type": "wait",
  "timestamp_ns": 3000000000,
  "delay_override_ms": null,
  "duration_ms": 500
}
```

> UI에서 수동 삽입. 고정 대기가 필요한 위치에 사용.

---

### 5-5. color_trigger ★ 로딩 감지 핵심 기능

```json
{
  "id": "e5f6a7b8",
  "type": "color_trigger",
  "timestamp_ns": 4000000000,
  "delay_override_ms": null,
  "x_ratio": 0.25,
  "y_ratio": 0.75,
  "target_color": "#FF0000",
  "tolerance": 10,
  "timeout_ms": 10000,
  "check_interval_ms": 50,
  "on_timeout": "error"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| x_ratio / y_ratio | float | 감지할 픽셀 좌표 (화면 비율) |
| target_color | string | 기다릴 목표 색상 (#RRGGBB) |
| tolerance | int | RGB 채널별 허용 오차 (기본 10). ±10 내면 일치 판정 |
| timeout_ms | int | 최대 대기 시간 |
| check_interval_ms | int | 폴링 주기 (기본 50ms) |
| on_timeout | string | "error"(재생 중단) \| "skip"(다음 진행) \| "retry"(처음부터) |

**구현 원리 — GetPixel, 스크린샷 아님:**
```python
# win32/hooks.py
def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
    hdc = ctypes.windll.user32.GetDC(0)
    color = ctypes.windll.gdi32.GetPixel(hdc, x, y)
    ctypes.windll.user32.ReleaseDC(0, hdc)
    return (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)

def color_matches(actual: tuple, target: tuple, tolerance: int) -> bool:
    return all(abs(a - t) <= tolerance for a, t in zip(actual, target))
```

---

### 5-6. window_trigger

```json
{
  "id": "f6a7b8c9",
  "type": "window_trigger",
  "timestamp_ns": 5000000000,
  "delay_override_ms": null,
  "window_title_contains": "완료",
  "timeout_ms": 10000,
  "on_timeout": "error"
}
```

> 특정 문자열을 제목에 포함한 창이 나타날 때까지 대기.
> Win32 FindWindow / EnumWindows 사용. 스크린샷 없음.

---

### 5-7. condition (스크립팅 — 조건 분기)

```json
{
  "id": "a7b8c9d0",
  "type": "condition",
  "timestamp_ns": 6000000000,
  "delay_override_ms": null,
  "expression": "pixel_color(0.25, 0.75) == '#FF0000'",
  "if_true": [ /* 이벤트 배열 (각 이벤트도 id 포함) */ ],
  "if_false": [ /* 이벤트 배열 */ ]
}
```

---

### 5-8. loop (스크립팅 — 반복)

```json
{
  "id": "b8c9d0e1",
  "type": "loop",
  "timestamp_ns": 7000000000,
  "delay_override_ms": null,
  "count": 5,
  "events": [ /* 반복할 이벤트 배열 */ ]
}
```

> count = -1이면 무한 반복. 중단은 핫키(기본 F12) 또는 timeout.

---

## 6. 완전한 예제 파일

```json
{
  "meta": {
    "version": "1.0",
    "app_version": "0.1.0",
    "created_at": "2025-01-15T14:30:00",
    "author": "Phillip",
    "description": "로그인 자동화 — 로딩 감지 포함",
    "screen_width": 1920,
    "screen_height": 1080,
    "dpi_scale": 1.0
  },
  "settings": {
    "click_dist_threshold_px": 8,
    "click_time_threshold_ms": 300,
    "default_playback_speed": 1.0,
    "color_trigger_check_interval_ms": 50,
    "color_trigger_default_timeout_ms": 10000
  },
  "raw_events": [
    {"id":"a1b2c3d4","type":"mouse_down","timestamp_ns":1000000000,"delay_override_ms":null,"x_ratio":0.5,"y_ratio":0.5,"button":"left"},
    {"id":"b2c3d4e5","type":"mouse_move","timestamp_ns":1020000000,"delay_override_ms":null,"x_ratio":0.501,"y_ratio":0.500},
    {"id":"c3d4e5f6","type":"mouse_up",  "timestamp_ns":1087000000,"delay_override_ms":null,"x_ratio":0.502,"y_ratio":0.501,"button":"left"},
    {"id":"d4e5f6a7","type":"color_trigger","timestamp_ns":2000000000,"delay_override_ms":null,"x_ratio":0.1,"y_ratio":0.9,"target_color":"#FFFFFF","tolerance":10,"timeout_ms":10000,"check_interval_ms":50,"on_timeout":"error"},
    {"id":"e5f6a7b8","type":"key_down",  "timestamp_ns":3000000000,"delay_override_ms":null,"key":"enter","vk_code":13},
    {"id":"f6a7b8c9","type":"key_up",    "timestamp_ns":3050000000,"delay_override_ms":null,"key":"enter","vk_code":13}
  ],
  "events": [
    {"id":"a1b2c3d4","type":"mouse_down","timestamp_ns":1000000000,"delay_override_ms":null,"x_ratio":0.5,"y_ratio":0.5,"button":"left"},
    {"id":"c3d4e5f6","type":"mouse_up",  "timestamp_ns":1087000000,"delay_override_ms":null,"x_ratio":0.502,"y_ratio":0.501,"button":"left"},
    {"id":"d4e5f6a7","type":"color_trigger","timestamp_ns":2000000000,"delay_override_ms":null,"x_ratio":0.1,"y_ratio":0.9,"target_color":"#FFFFFF","tolerance":10,"timeout_ms":10000,"check_interval_ms":50,"on_timeout":"error"},
    {"id":"e5f6a7b8","type":"key_down",  "timestamp_ns":3000000000,"delay_override_ms":100,"key":"enter","vk_code":13},
    {"id":"f6a7b8c9","type":"key_up",    "timestamp_ns":3050000000,"delay_override_ms":null,"key":"enter","vk_code":13}
  ],
  "is_edited": true
}
```

> 위 예제에서:
> - raw_events[1] (mouse_move, id=b2c3d4e5) 이 events에서 제거됨
> - events의 key_down (id=e5f6a7b8) 에 delay_override_ms=100 이 설정됨
> - raw_events는 원본 그대로 보존됨
> - id로 raw↔events 간 대응 추적 가능

---

## 7. 이벤트 타입 전체 요약

| type | 생성 주체 | 설명 |
|---|---|---|
| mouse_down | 녹화 자동 | 마우스 버튼 누름 |
| mouse_up | 녹화 자동 | 마우스 버튼 뗌 |
| mouse_move | 녹화 자동 | 마우스 이동 (events에서 일괄 삭제 가능) |
| key_down | 녹화 자동 | 키 누름 |
| key_up | 녹화 자동 | 키 뗌 |
| wait | UI 수동 삽입 | 고정 대기 |
| color_trigger | UI 수동 삽입 | 픽셀 색 감지 대기 ★ |
| window_trigger | UI 수동 삽입 | 창 제목 감지 대기 |
| condition | UI 수동 삽입 | 조건 분기 |
| loop | UI 수동 삽입 | 반복 실행 |

---

## 8. 스키마 버전 마이그레이션

- meta.version이 앱 버전과 다르면 macro_file.py가 MIGRATIONS 딕셔너리에서 함수 호출
- 로드 시 즉시 현재 버전으로 변환, 메모리에서 처리
- 저장 시 항상 최신 버전으로 저장 (덮어쓰기 전 .bak 자동 생성)

---

## 9. UI 편집 기능 — JSON 관점 정리

| UI 동작 | JSON 변화 |
|---|---|
| mouse_move 일괄 삭제 | events에서 type=="mouse_move" 제거. raw_events 유지. is_edited=true |
| 딜레이 개별 수정 | events 내 해당 id의 delay_override_ms 설정 |
| 딜레이 일괄 수정 | events 전체 delay_override_ms를 동일값으로 설정 |
| delay_override_ms → null | 해당 이벤트 원래 타이밍 복원 |
| 원본으로 되돌리기 | events = raw_events 전체 복사. is_edited=false |
| 저장 | 현재 events 기준 저장. 덮어쓰기 전 .bak 생성 |
