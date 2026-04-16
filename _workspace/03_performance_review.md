# 성능 리뷰

## 리뷰 개요
- **성능 수준 평가**: 🟡 개선 여지
- **총 발견 수**: 🔴 3 / 🟡 6 / 🟢 3

---

## 성능 이슈 발견 사항

### 🔴 필수 최적화

---

#### 1. **[sendinput.py:110–113]** — 좌표 변환 매 이벤트마다 `get_logical_screen_size()` 호출
- **문제**: `_normalize(x, y)` 가 호출될 때마다 `get_logical_screen_size()` 를 실행한다. 이 함수는 내부적으로 Win32 API (`GetSystemMetrics` 또는 동등 호출)를 매번 호출하는 구조일 가능성이 높으며, 재생 루프에서 마우스 이동 이벤트 하나당 최소 1회씩 발생한다.
- **영향**: 빠른 마우스 이동 구간(초당 수십 건)에서 syscall 오버헤드가 누적되어 재생 타이밍 정밀도에 수 ms 영향을 줄 수 있다.
- **현재 코드**:
  ```python
  def _normalize(x: int, y: int) -> tuple[int, int]:
      w, h = get_logical_screen_size()   # 매 호출마다 syscall
      nx = x * 65535 // max(w - 1, 1)
      ny = y * 65535 // max(h - 1, 1)
      return (nx, ny)
  ```
- **최적화 코드**:
  ```python
  # 모듈 초기화 시점에 한 번만 읽고 캐싱
  _screen_w: int
  _screen_h: int

  def _init_screen_size() -> None:
      global _screen_w, _screen_h
      _screen_w, _screen_h = get_logical_screen_size()

  def _normalize(x: int, y: int) -> tuple[int, int]:
      nx = x * 65535 // max(_screen_w - 1, 1)
      ny = y * 65535 // max(_screen_h - 1, 1)
      return (nx, ny)
  ```
- **개선 효과**: 재생 중 syscall 횟수를 O(N) → O(1)으로 감소. 빠른 마우스 이동 구간에서 타이밍 안정성 향상.
- **트레이드오프**: 해상도 변경(다중 모니터 전환, DPI 변경) 이벤트를 별도로 구독해서 캐시를 무효화해야 한다. 일반 사용 시나리오(단일 모니터, DPI 고정)에서는 위험 없음.

---

#### 2. **[sendinput.py:184–188]** — `send_mouse_drag()` 내부 `time.sleep(0.01)` — 재생 루프 타이밍 기준 위반
- **문제**: 드래그 보간 루프 안에서 `time.sleep(0.01)` 을 10회 호출한다. 총 ~100ms 블로킹이 발생하며, player.py 의 절대 타임스탬프 드리프트 보정 루프 바깥에서 일어나는 sleep이므로 보정 대상이 아니다. 즉, 드래그 이후의 모든 이벤트가 ~100ms 이상 지연된다.
- **영향**: 드래그 이벤트가 포함된 매크로에서 이후 이벤트 타이밍이 100ms 이상 틀어진다. `core-beliefs.md 원칙 3 (time.sleep 반복 금지)` 위반.
- **현재 코드**:
  ```python
  for i in range(1, steps + 1):
      mx = x1 + (x2 - x1) * i // steps
      my = y1 + (y2 - y1) * i // steps
      _send(_mouse_input(mx, my, MOUSEEVENTF_MOVE))
      time.sleep(0.01)   # <- 타이밍 보정 밖의 sleep
  ```
- **최적화 코드**:
  ```python
  # sleep 제거 후 단일 SendInput 배치 호출로 대체
  def send_mouse_drag(x1, y1, x2, y2, button="left"):
      down_flag, up_flag = _BUTTON_FLAGS.get(button, _BUTTON_FLAGS["left"])
      steps = 10
      inputs = [
          _mouse_input(x1, y1, MOUSEEVENTF_MOVE),
          _mouse_input(x1, y1, down_flag),
      ]
      for i in range(1, steps + 1):
          mx = x1 + (x2 - x1) * i // steps
          my = y1 + (y2 - y1) * i // steps
          inputs.append(_mouse_input(mx, my, MOUSEEVENTF_MOVE))
      inputs.append(_mouse_input(x2, y2, up_flag))
      _send(*inputs)   # 원자적 전송
  ```
- **개선 효과**: 드래그 실행 시간 100ms → <1ms. 이후 이벤트 타이밍 드리프트 제거.
- **트레이드오프**: 일부 대상 앱(게임 등)은 이동 이벤트 사이 딜레이를 요구할 수 있다. 필요 시 `drag_step_delay_ms` 파라미터를 옵션으로 제공하되 기본값 0으로 설정.

---

#### 3. **[hooks.py:379–382]** — `get_pixel_color()` 가 매 호출마다 GetDC/ReleaseDC — 예외 시 GDI 핸들 누수
- **문제**: `get_pixel_color()` 는 호출할 때마다 `GetDC(None)` → `GetPixel` → `ReleaseDC(None)` 을 순서대로 실행한다. `GetPixel` 이 예외를 발생시키면 `ReleaseDC` 가 호출되지 않아 GDI 핸들이 누수된다. 색 트리거 폴링 루프에서 반복 호출되므로 누수가 누적된다.
- **영향**: 예외 경로에서 GDI 핸들 누수 → 장시간 실행 시 GDI 자원 고갈.
- **현재 코드**:
  ```python
  def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
      hdc = _user32.GetDC(None)
      color = _gdi32.GetPixel(hdc, x, y)
      _user32.ReleaseDC(None, hdc)   # 예외 시 미실행
      return (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)
  ```
- **최적화 코드**:
  ```python
  def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
      hdc = _user32.GetDC(None)
      try:
          color = _gdi32.GetPixel(hdc, x, y)
      finally:
          _user32.ReleaseDC(None, hdc)
      return (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)
  ```
- **개선 효과**: 예외 경로에서도 GDI 핸들 누수 완전 방지. 장시간 실행 안정성 향상.
- **트레이드오프**: 없음.

---

### 🟡 권장 최적화

---

#### 4. **[editor.py:110–322]** — `_build_rows()` 의 O(N²) 내부 루프 — 대규모 이벤트 리스트 시 UI 프리즈
- **문제**: `_build_rows` 는 각 `mouse_down` 이벤트마다 이후 이벤트를 선형 스캔(`for j in range(i + 1, len(events))`)하여 대응하는 `mouse_up`을 찾는다. 이벤트 수 N개에서 최악 O(N²) 복잡도.
- **영향**: 1만 개 이상의 마우스 이벤트(드래그 중 이동 포함) 로드 시 `_refresh()` 가 메인 스레드에서 실행되어 UI 수 초 블로킹.
- **현재 코드**: editor.py:125–167 mouse_down 처리 블록 — 내부 선형 스캔
- **최적화 코드**:
  ```python
  # 전처리: button -> up 이벤트 인덱스를 미리 매핑 (O(N))
  up_map: dict[int, int] = {}
  pending: dict[str, int] = {}
  for idx, e in enumerate(events):
      if isinstance(e, MouseButtonEvent):
          if e.type == "mouse_down":
              pending[e.button] = idx
          elif e.type == "mouse_up" and e.button in pending:
              up_map[pending.pop(e.button)] = idx
  # 이후 down 처리에서 up_map[i] 로 O(1) 조회
  ```
- **개선 효과**: 1만 이벤트 기준 빌드 시간 약 100ms → <5ms 예상.
- **트레이드오프**: 구현 복잡도 소폭 증가.

---

#### 5. **[recorder.py:224–248]** — `_consumer_loop()` 의 1ms busy-wait 폴링
- **문제**: 소비자 루프가 큐가 비었을 때 `time.sleep(0.001)` (1ms)로 폴링한다. GIL 해제/획득을 초당 1000회 반복하는 오버헤드 발생.
- **영향**: 유휴 구간에서 불필요한 CPU 사이클 소모. 멀티코어 환경에서 HookPump 스레드와 경쟁 가능.
- **현재 코드**:
  ```python
  else:
      time.sleep(0.001)  # 1ms 폴링
  ```
- **최적화 코드**:
  ```python
  # 슬립 간격을 5ms로 늘려 CPU 부하 감소 (타이밍 영향 없음)
  # 또는 queue.SimpleQueue + get(timeout=0.005) 패턴으로 완전 대체
  time.sleep(0.005)
  ```
- **개선 효과**: 유휴 시 CPU 사용률 감소. 이벤트 처리 지연(최대 +4ms)은 허용 범위 내.
- **트레이드오프**: 고빈도 입력 시 큐 크기가 커질 수 있으나, 5ms 누적은 녹화 타임스탬프 정밀도에 영향 없음(타임스탬프는 Hook 콜백에서 즉시 기록).

---

#### 6. **[editor.py:578–596]** — `highlight_event()` 의 O(N) 행 선형 탐색
- **문제**: 재생 중 이벤트 인덱스를 받을 때마다 `_rows` 전체를 선형 탐색하여 대응하는 행을 찾는다. 재생 속도와 이벤트 밀도에 따라 초당 수십~수백 회 호출 가능.
- **영향**: 수천 행 이상에서 하이라이트 연산마다 O(N) 비용. 빠른 재생(5x 이상)에서 UI 스레드 부하 증가.
- **현재 코드**:
  ```python
  for row_idx, row in enumerate(self._rows):
      if event_idx in row.event_indices:
          ...
          return
  ```
- **최적화 코드**:
  ```python
  # _refresh() 시점에 역방향 인덱스 빌드 (O(N), 1회)
  self._event_to_row: dict[int, int] = {
      eidx: row_idx
      for row_idx, row in enumerate(self._rows)
      for eidx in row.event_indices
  }
  # highlight_event 에서 O(1) 조회
  row_idx = self._event_to_row.get(event_idx, -1)
  ```
- **개선 효과**: 하이라이트 탐색 O(N) → O(1). 고속 재생 시 UI 응답성 개선.
- **트레이드오프**: `_refresh()` 시 추가 dict 생성 비용 (O(N), 1회).

---

#### 7. **[player.py:263]** — `list(enumerate(all_events))[start:end]` — 전체 리스트 복사 후 슬라이싱
- **문제**: 구간 재생을 위해 전체 이벤트에 대해 `list(enumerate(all_events))` 로 복사본을 생성한 뒤 슬라이싱한다. 이벤트 수가 많으면 불필요한 메모리 할당 발생.
- **영향**: 1만 이벤트 기준 수백 KB 임시 할당 및 GC 압력.
- **현재 코드**:
  ```python
  events_to_play = list(enumerate(all_events))[start:end]
  ```
- **최적화 코드**:
  ```python
  events_to_play = list(enumerate(all_events[start:end], start=start))
  ```
- **개선 효과**: 불필요한 전체 리스트 복사 제거. 코드 의도도 더 명확.
- **트레이드오프**: 없음.

---

#### 8. **[recorder.py:371]** — `get_event_count()` 의 락 미사용
- **문제**: `get_event_count()` 는 `_event_buffer_lock` 없이 `len(_event_buffer)` 를 직접 읽는다. CPython GIL이 `len()` 원자성을 보장하지만 명시적이지 않음.
- **영향**: 현재 CPython에서는 실제 경쟁 조건 없음. 이론적 안전성 미흡.
- **현재 코드**: `return len(_event_buffer)`
- **최적화 코드**: `with _event_buffer_lock: return len(_event_buffer)`
- **개선 효과**: 명시적 스레드 안전성 보장.
- **트레이드오프**: 폴링(250ms 주기)에서 미세한 lock 경쟁 추가 — 실질적 영향 없음.

---

#### 9. **[player.py:275–276]** — 일시정지 감지 루프 50ms 슬립
- **문제**: 일시정지 중 `time.sleep(0.05)` 로 폴링하여 resume 시 최대 50ms 지연.
- **영향**: resume 응답 지연 최대 50ms. 타이밍 정밀도 앱에서 사용자 경험 저하.
- **현재 코드**: `time.sleep(0.05)`
- **최적화 코드**:
  ```python
  # _pause_flag 와 별도로 _resume_event: threading.Event 사용
  _resume_event.wait(timeout=0.05)  # 신호 받으면 즉시 깨어남
  ```
- **개선 효과**: resume 응답 지연 50ms → <1ms.
- **트레이드오프**: 신호 체계 복잡도 소폭 증가.

---

### 🟢 참고 / 미래 고려

---

#### 10. **[recorder.py:317]** — `copy.deepcopy(raw_events)` — 녹화 종료 시 전체 이벤트 복사
- **현황**: `stop_recording()` 에서 `raw_events` 전체를 `deepcopy` 한다. 장시간 녹화(수만 이벤트) 시 "stopping" 상태가 수백 ms 지속될 수 있다. 현재는 `RecStopWorker` 스레드에서 수행되므로 UI 블로킹 없음.
- **고려**: 이벤트 수가 수십만 건에 달할 경우 지연 문제가 생길 수 있으므로, 필요 시 COW(Copy-on-Write) 전략 또는 lazy copy 도입 고려.

---

#### 11. **[script_engine.py:571–580]** — `execute_loop()` 무한 루프 시 stop_flag 확인 간격
- **현황**: `stop_flag` 확인이 서브 이벤트 단위로만 이루어진다. 서브 이벤트 자체가 긴 `WaitEvent`(수 초)이면 stop 응답이 지연된다.
- **고려**: `WaitEvent` 실행 시 내부에서도 stop_flag 폴링 추가 검토.

---

#### 12. **[hooks.py:405–423]** — `find_window()` 내부 매 호출 시 `_WNDENUMPROC` 재생성
- **현황**: `find_window()` 는 호출마다 `_WNDENUMPROC` 콜백 객체를 새로 생성한다. `_wait_for_window` 폴링 루프에서 반복 호출 시 ctypes 콜백 객체 생성/해제 반복.
- **고려**: 정확한 제목 매칭이 가능하다면 `FindWindowW` API로 교체하여 `EnumWindows` 오버헤드 제거 고려.

---

## 복잡도 분석

| 함수 | 시간 복잡도 | 공간 복잡도 | 호출 빈도 | 우선순위 |
|---|---|---|---|---|
| `_build_rows()` (editor.py:110) | O(N²) 최악 | O(N) | 로드/편집 시 | 🔴 높음 |
| `highlight_event()` (editor.py:578) | O(N) | O(1) | 재생 이벤트마다 | 🟡 중간 |
| `_normalize()` (sendinput.py:109) | O(1) + syscall | O(1) | 매 마우스 이벤트 | 🔴 높음 |
| `_play_loop()` (player.py:227) | O(N) | O(1) | 재생 1회 | 🟢 양호 |
| `_consumer_loop()` (recorder.py:223) | O(1)/iter | O(N) | 연속 폴링 | 🟡 중간 |
| `send_mouse_drag()` (sendinput.py:166) | O(steps)=O(1) | O(1) | 드래그마다 | 🔴 높음 (sleep) |
| `execute_loop()` (script_engine.py:556) | O(count×N) | O(1) | 루프 이벤트 시 | 🟢 양호 |
| `get_pixel_color()` (hooks.py:367) | O(1) + 2 syscall | O(1) | 색 트리거 폴링 | 🟡 중간 |
| `_refresh()` (editor.py:683) | O(N) | O(N) | 편집마다 | 🟢 양호 |
| `find_window()` (hooks.py:396) | O(W) W=창수 | O(1) | 창 트리거 폴링 | 🟢 양호 |

---

## 동시성 안전성 분석

### 공유 상태 목록

| 변수 | 위치 | 접근 스레드 | 보호 수단 | 위험도 |
|---|---|---|---|---|
| `_current_event_idx` | player.py:69 | PlaybackThread(write) / UI(read) | 없음 | 🟡 |
| `_total_events` | player.py:70 | PlaybackThread(write) / UI(read) | 없음 | 🟡 |
| `_stop_flag` | player.py:67 | 다수 스레드 | `threading.Event` | 🟢 |
| `_pause_flag` | player.py:68 | 다수 스레드 | `threading.Event` | 🟢 |
| `_event_buffer` | recorder.py:124 | RecorderConsumer(write) / UI(read) | `_event_buffer_lock` | 🟢 |
| `_recording` | recorder.py:119 | 메인 스레드 전용 | 없음 (단일 스레드) | 🟢 |

### 주요 동시성 이슈

**1. `_current_event_idx` / `_total_events` 락 없는 읽기**
- `get_progress()` 와 `get_current_event_idx()` 는 `_total_events`, `_current_event_idx` 를 락 없이 읽는다.
- `_play_loop()` 가 이를 쓰는 스레드이고 UI 타이머(250ms)가 읽는다.
- CPython GIL이 int 할당 원자성을 보장하므로 실용적 위험은 낮다. 단, `_total_events` 를 읽고 나서 `_current_event_idx` 를 읽는 사이 값이 바뀌면 `get_progress()` 가 1.0 초과를 반환할 수 있다.
- **권고**: `get_progress()` 내부에서 두 값을 한 번에 스냅샷으로 읽거나, 값을 단일 구조체로 묶어 관리.

**2. `stop()` 함수의 중복 재생 시작 경쟁**
```python
def stop() -> None:
    _stop_flag.set()
    _pause_flag.clear()
    if _playback_thread is not None:
        _playback_thread.join(timeout=3.0)
    _stop_flag.clear()
```
- `stop()` 이 반환된 직후 `play()` 를 즉시 호출하면 새 PlaybackThread 시작 전에 기존 스레드가 아직 종료 중일 수 있다. 특히 `join(timeout=3.0)` 이 타임아웃으로 반환된 경우 이전 PlaybackThread가 살아있는 채로 새 스레드가 시작되어 **두 PlaybackThread가 동시에 실행**될 수 있다.
- **권고**: `play()` 진입 시 `_playback_thread.is_alive()` 확인 후 필요 시 stop() 호출 가드 추가.

**3. `FlowEngine._run_macro_node()` 의 50ms 폴링 wait**
```python
while not done_event.is_set() and not self._stop_flag.is_set():
    time.sleep(0.05)
```
- `threading.Event.wait(timeout=0.05)` 사용으로 대체하면 완료 즉시 깨어날 수 있다.

**4. `_emg_keyboard_proc` 내 `_emg_callback()` 직접 호출**
- LL Hook 콜백 스레드에서 `_emg_callback()` (= Qt Signal emit)이 직접 실행된다.
- PyQt6 cross-thread signal은 기본적으로 QueuedConnection이므로 안전하나, Hook 콜백 스레드의 실행 시간을 늘린다. 최소 처리 원칙 관점에서 개선 여지 있음.

---

## 타이밍 정밀도 분석

### 재생 타이밍 메커니즘 평가

**절대 타임스탬프 기반 재생 (player.py:289–296)**
```python
target_ns = play_start_ns + int((event.timestamp_ns - base_ts_ns) / speed)
now_ns = time.perf_counter_ns()
sleep_ns = target_ns - now_ns
if sleep_ns > 1_000_000:
    time.sleep(sleep_ns / 1_000_000_000)
```
- `time.perf_counter_ns()` 사용: 올바름. Windows에서 100ns 미만 해상도.
- 1ms 미만 sleep 스킵: 올바름. `time.sleep` 최소 정밀도(~15ms Windows)를 고려한 적절한 처리.
- **누적 드리프트 없음**: 각 이벤트가 독립적으로 절대 타임스탬프를 기준으로 계산되므로 누적 오차 없음. 설계 우수.

**드리프트 보정 (player.py:327–333)**
- 색/창 트리거 실행 후 `play_start_ns` 를 실제 경과 시간만큼 전진시켜 상대 타이밍 유지. 올바른 보정.

**실제 타이밍 오차 원인 (우선순위 순)**
1. `send_mouse_drag()` 내 `time.sleep(0.01) × 10`: 100ms 강제 드리프트 유발 — 🔴 즉시 수정 필요
2. Windows 기본 타이머 해상도 15.6ms: `time.sleep(sleep_ns)` 호출 시 ±15ms 오버슛 가능. `timeBeginPeriod(1)` 로 1ms 해상도로 개선 가능하나 시스템 전체에 영향.
3. GIL 경쟁: PlaybackThread가 sleep에서 깨어날 때 GIL을 즉시 획득하지 못하면 수 ms 추가 지연 가능.
4. `_execute_event()` 내 `WaitEvent` → `time.sleep(event.duration_ms / 1000.0)`: 절대 타임스탬프 보정 루프 밖의 sleep이나, 다음 이벤트의 `target_ns` 가 절대값이므로 자동 보정됨.

**타이밍 정밀도 종합 평가**: 🟡
- 기본 메커니즘(절대 타임스탬프 + 드리프트 보정)은 설계 우수.
- `send_mouse_drag()` 의 내부 sleep이 핵심 정밀도 저해 요인.
- Windows 기본 타이머 해상도(15.6ms) 개선 미적용 — 향후 고려 필요.

---

## 프로파일링 권고

| 대상 | 도구 | 이유 |
|---|---|---|
| `_build_rows()` | `cProfile` + `snakeviz` | 이벤트 1만 건 이상 로드 시 UI 응답 측정 |
| `_normalize()` + `send_mouse_move()` | `time.perf_counter_ns()` 수동 계측 | 마우스 이동 이벤트당 syscall 오버헤드 정량화 |
| `PlaybackThread` 전체 | `py-spy` (샘플링) | 실제 재생 중 타이밍 분포 확인 |
| `_consumer_loop()` | logging timestamp 삽입 | GIL 대기 vs. sleep 비율 확인 |
| `highlight_event()` | Qt 프레임 타이머 (`QElapsedTimer`) | 고속 재생(5x)에서 UI 프레임드롭 여부 확인 |
| Windows 타이머 해상도 | `timeBeginPeriod(1)` 전후 `time.sleep(0.001)` 실측 | 1ms sleep 오버슛 정도 측정 |
