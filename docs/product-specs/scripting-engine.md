# scripting-engine.md — 스크립팅 엔진 스펙

---

## 1. 설계 방향 및 범위 결정

### 핵심 결정
스크립팅의 주 인터페이스는 **비주얼 플로우차트 시퀀서**다.
"JSON 파일(매크로) + 조건(color_trigger) + 분기"를 GUI에서 마우스로 조립하는 방식.
별도의 텍스트 DSL이나 코드 편집기는 MVP에 포함하지 않는다.

### MVP 범위 (구현)
- color_trigger 기반 조건 분기 (success / failure 경로 분기)
- 매크로 파일 단위 반복 실행 (플로우차트 레벨 loop)
- 변수: 단순 카운터만 지원 (반복 횟수 추적용)

### Phase2 범위 (기술 부채로 등록)
- 복잡한 변수 시스템 (string, coordinate 타입)
- if/else 중첩 분기
- UI Automation 기반 트리거
- 텍스트 DSL 편집기

---

## 2. 조건 노드 타입 (플로우차트에서 사용)

### 2-1. color_check (핵심 조건 — 스냅샷 없음)

```json
{
  "id": "cond_a1b2",
  "type": "color_check",
  "x_ratio": 0.25,
  "y_ratio": 0.75,
  "target_color": "#FFFFFF",
  "tolerance": 10,
  "check_interval_ms": 50,
  "timeout_ms": 10000,
  "on_match": "next_node_id_A",
  "on_timeout": "next_node_id_B"
}
```

| 필드 | 설명 |
|---|---|
| on_match | 색이 일치하면 이동할 다음 노드 id |
| on_timeout | timeout 초과 시 이동할 다음 노드 id (null이면 팝업) |

**동작 원리**: GetPixel Win32 API로 단일 픽셀 RGB 읽기. 스크린샷 아님.

### 2-2. counter (반복 제어용 변수)

```json
{
  "id": "counter_c3d4",
  "type": "counter",
  "name": "row_count",
  "initial": 0,
  "increment": 1,
  "max": 100,
  "on_continue": "next_node_id_A",
  "on_max_reached": "next_node_id_B"
}
```

max에 도달하면 on_max_reached 경로로 분기. 미달이면 on_continue 경로로.
플로우차트에서 "100개 종목 처리 완료까지 반복" 같은 패턴에 사용.

### 2-3. wait_fixed (고정 대기)

```json
{
  "id": "wait_e5f6",
  "type": "wait_fixed",
  "duration_ms": 1000,
  "next": "next_node_id"
}
```

---

## 3. 실행 엔진 — 플로우차트 순회

```python
class FlowEngine:
    def run(self, flow: MacroFlow) -> None:
        current_id = flow.start_node_id

        while current_id is not None:
            node = flow.nodes[current_id]

            if node.type == "macro":
                result = self._run_macro(node.macro_path)
                current_id = node.next_on_success if result.ok \
                             else node.next_on_failure

            elif node.type == "color_check":
                matched = self._wait_for_color(node)
                current_id = node.on_match if matched else node.on_timeout

            elif node.type == "counter":
                node.value += node.increment
                current_id = node.on_continue if node.value < node.max \
                             else node.on_max_reached

            elif node.type == "wait_fixed":
                time.sleep(node.duration_ms / 1000)
                current_id = node.next

            elif node.type == "end":
                break
```

---

## 4. 플로우 파일 포맷 (.macroflow)

플로우차트는 개별 매크로 JSON과 별도로 `.macroflow` 확장자로 저장.

```json
{
  "meta": {
    "version": "1.0",
    "name": "종목 일괄 조회",
    "created_at": "2025-01-15T14:00:00"
  },
  "start_node_id": "macro_start",
  "nodes": {
    "macro_start": {
      "type": "macro",
      "label": "로그인",
      "macro_path": "login.json",
      "position": {"x": 100, "y": 100},
      "next_on_success": "color_loading",
      "next_on_failure": "end_error"
    },
    "color_loading": {
      "type": "color_check",
      "label": "로딩 완료 대기",
      "x_ratio": 0.1, "y_ratio": 0.9,
      "target_color": "#FFFFFF",
      "tolerance": 10,
      "timeout_ms": 15000,
      "check_interval_ms": 50,
      "position": {"x": 100, "y": 250},
      "on_match": "macro_query",
      "on_timeout": "end_error"
    },
    "macro_query": {
      "type": "macro",
      "label": "종목 조회",
      "macro_path": "query.json",
      "position": {"x": 100, "y": 400},
      "next_on_success": "counter_rows",
      "next_on_failure": "end_error"
    },
    "counter_rows": {
      "type": "counter",
      "label": "행 카운터",
      "name": "row_count",
      "initial": 0,
      "increment": 1,
      "max": 100,
      "position": {"x": 100, "y": 550},
      "on_continue": "macro_query",
      "on_max_reached": "end_success"
    },
    "end_success": {
      "type": "end",
      "label": "완료",
      "position": {"x": 100, "y": 700},
      "status": "success"
    },
    "end_error": {
      "type": "end",
      "label": "오류 종료",
      "position": {"x": 350, "y": 400},
      "status": "error"
    }
  }
}
```

---

## 5. 샌드박스 보안 원칙

- 스크립팅 엔진은 파일시스템 접근 불가 (매크로 파일 로드만 허용)
- 네트워크 접근 불가
- 허용 함수: get_pixel_color(), wait(), counter 조작
- eval() / exec() 사용 금지 (Phase2 DSL 추가 시에도 샌드박스 필수)
