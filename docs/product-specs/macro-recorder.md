# macro-recorder.md — 녹화 기능 스펙

---

## 1. 녹화 UX 흐름

```
[대기 상태]
  → 토글 단축키(기본 F6) 누름
  → 미니 오버레이 창 표시 (우하단, 항상 최상위)
  → 3초 카운트다운 후 녹화 시작
  → raw_events 수집 시작

[녹화 중]
  → 미니 오버레이: 빨간 점 깜빡임 + 경과 시간 + 이벤트 수 표시
  → 토글 단축키 다시 누름 → 녹화 중지
  → 자동 임시 저장 (~/.macroflow/temp/recording_YYYYMMDD_HHMMSS.json)
  → 메인 창 에디터 탭으로 포커스 이동 (임시 파일 자동 로드)
  → 미니 오버레이 사라짐

[긴급 중단 — ESC 3회 연속 (500ms 이내)]
  → 녹화 또는 재생 중 어느 상태에서든 즉시 전체 중지
  → 녹화 중이었다면: 임시 저장 수행 후 중단
  → 재생 중이었다면: 즉시 중단, 저장 없음
  → 비프음(시스템 MB_ICONHAND) 으로 중단 피드백
```

---

## 2. 단축키 설계

| 동작 | 기본 단축키 | 비고 |
|---|---|---|
| 녹화 시작/중지 토글 | F6 | 설정에서 변경 가능 |
| 재생 시작/중지 토글 | F7 | 설정에서 변경 가능 |
| 긴급 전체 중지 | ESC × 3회 (500ms 이내) | 변경 불가 고정 |

### 단축키 충돌 방지 전략
- F6/F7은 대부분의 업무용 앱에서 사용 빈도가 낮아 기본값으로 채택
- 단축키 변경 UI에서 다른 앱과 충돌 여부를 실시간으로 감지해 경고 표시
- 단축키 자체(F6 key_down/key_up)는 raw_events에 기록하지 않음
  → Win32 LL Hook 콜백에서 단축키 감지 즉시 `CallNextHookEx` 체인 차단

### ESC 3회 연속 감지 로직
```python
# recorder.py / player.py 공통 적용
ESC_VK = 0x1B
ESC_WINDOW_MS = 500

esc_times: deque[int] = deque(maxlen=3)  # 최근 3회 ESC 타임스탬프(ms)

def on_key_down(vk_code: int, timestamp_ns: int) -> bool:
    if vk_code == ESC_VK:
        now_ms = timestamp_ns // 1_000_000
        esc_times.append(now_ms)
        if len(esc_times) == 3 and (esc_times[-1] - esc_times[0]) <= ESC_WINDOW_MS:
            trigger_emergency_stop()
            return True  # 이벤트 체인 차단 (raw_events에 기록 안 함)
    return False
```

---

## 3. 미니 오버레이 창 (녹화/재생 중 전용)

### 목적
- 녹화·재생 중 사용자가 다른 앱을 조작하는 데 방해가 되지 않아야 함
- 현재 상태(녹화 중 / 재생 중)를 항상 인지할 수 있어야 함
- 이 창 자체의 이벤트는 raw_events에 절대 기록되지 않음

### 크기 및 위치
- 크기: 180 × 48px (고정, 리사이즈 불가)
- 위치: 화면 우측 하단, 작업 표시줄 위 8px
- 항상 최상위(WS_EX_TOPMOST) + 클릭 투과(WS_EX_TRANSPARENT) 선택 가능
- 위치는 드래그로 이동 가능, 마지막 위치 저장

### 녹화 중 표시 요소
```
[ ● REC  00:12  #247 ]
  ↑        ↑      ↑
빨간점   경과시간  이벤트수
깜빡임
```
- 빨간 점(●): 1초 주기 깜빡임
- 경과 시간: MM:SS
- 이벤트 수: 누적 raw_events 카운트
- 토글 단축키(F6): 클릭 가능한 중지 버튼으로도 기능

### 재생 중 표시 요소
```
[ ▶ PLAY  67%  1.0x ]
  ↑         ↑    ↑
초록화살  진행률  속도
```

### 이 창의 이벤트가 raw_events에 기록되지 않는 이유
미니 오버레이 창은 `WS_EX_NOACTIVATE` 스타일로 생성하여
포커스를 가져가지 않음. LL Hook 콜백에서 이벤트 발생 시
`GetForegroundWindow()` 와 오버레이 HWND를 비교해 일치하면 기록 제외.

---

## 4. 녹화 엔진 동작 원칙

### 이벤트 캡처
- Win32 `WH_MOUSE_LL` + `WH_KEYBOARD_LL` 단일 메시지 펌프 스레드에서 처리
- 콜백에서는 `perf_counter_ns()` 타임스탬프 찍고 deque push만 수행
- 소비자 스레드가 deque에서 pop → MacroEvent 변환 → raw_events 버퍼 적재

### 무조건 기록하는 것 (판별 금지)
- mouse_down, mouse_up, mouse_move, key_down, key_up 전부 RAW 저장
- 클릭/드래그 판별 금지 (core-beliefs.md 원칙 1)
- mouse_move 필터링 금지 (core-beliefs.md 원칙 8)

### 기록하지 않는 것
- 토글 단축키(F6, F7) key_down / key_up
- ESC 3회 연속 시퀀스의 ESC 이벤트
- 미니 오버레이 창(HWND 매칭)에서 발생한 이벤트
- 카운트다운(3초) 중 발생한 이벤트

### 좌표 처리
- dpi.py의 `pixel_to_ratio()` 로 모든 좌표를 비율(0.0~1.0)로 변환
- 녹화 시작 시 `get_logical_screen_size()` 를 meta에 기록

---

## 5. 임시 저장 및 자동 복구

### 임시 저장 경로
```
%APPDATA%\MacroFlow\temp\recording_YYYYMMDD_HHMMSS.json
```

### 임시 저장 시점
- 녹화 중지 직후 즉시 자동 저장
- 앱 비정상 종료 대비: 녹화 중 30초마다 중간 임시 저장
  (`recording_YYYYMMDD_HHMMSS.tmp` → 완료 시 `.json`으로 변경)

### 앱 재시작 시 자동 복구
- 시작 시 temp/ 폴더에 미처리 `.json` 파일 있으면 복구 알림
- "복구할게요 / 버릴게요" 다이얼로그 표시

### 정식 저장
- 에디터에서 편집 완료 후 Ctrl+S 또는 "저장" 버튼
- 파일 이름: 사용자 지정 (기본값: recording_YYYYMMDD_HHMMSS)
- 저장 경로: 마지막 저장 경로 기억
- 저장 시 .bak 자동 생성 (json-format-spec.md 참조)

---

## 6. 성능 요구사항

| 항목 | 목표값 |
|---|---|
| 이벤트 손실률 | 0% (LL Hook 단일 펌프로 보장) |
| 타임스탬프 정밀도 | 나노초 (perf_counter_ns) |
| 콜백 처리 시간 | < 0.1ms (deque push만 수행) |
| CPU 사용률 (녹화 중) | < 3% |
| 메모리 (이벤트 10만개 기준) | < 50MB |

---

## 7. 엣지케이스 처리

| 상황 | 처리 방법 |
|---|---|
| 녹화 중 PC 절전 모드 진입 | 절전 복귀 후 녹화 자동 중지 + 임시 저장 |
| 녹화 중 모니터 해상도 변경 | 변경 감지 시 녹화 중지 + 경고 ("해상도 변경 감지, 재생 시 좌표가 어긋날 수 있습니다") |
| 멀티모니터 환경 | 가상 스크린 전체 좌표계 사용. meta에 모니터 구성 기록 |
| 녹화 중 UAC 권한 상승 창 | LL Hook이 UAC 창 이벤트를 캡처하지 못함. 경고 표시 후 계속 녹화 |
