---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/types.py"
type: "code"
community: "MacroData MouseButtonEvent KeyEvent MacroSettings"
location: "L141"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings
---

# WindowTriggerEvent

## Connections
- [[RRGGBB 문자열을 (R, G, B) 튜플로 변환한다._1]] - `uses` [INFERRED]
- [[Build the deterministic MacroFlow scenario used by the RDP smoke test.]] - `uses` [INFERRED]
- [[ConditionLoop 내부 이벤트를 top-level과 같은 시간 규칙으로 실행한다.]] - `uses` [INFERRED]
- [[Contract tests for the Windows RDP GUI smoke harness.]] - `uses` [INFERRED]
- [[Event editor display row construction.  This module intentionally stays free of]] - `uses` [INFERRED]
- [[JSON 파일에서 MacroData를 로드한다.      마이그레이션이 필요한 경우 자동으로 수행한다.      Args         pat]] - `uses` [INFERRED]
- [[MacroData를 JSON 파일로 저장한다.      기존 파일이 있으면 .bak으로 백업 후 덮어쓴다.      Args         m]] - `uses` [INFERRED]
- [[MacroData를 별도 스레드에서 재생 시작한다.      Args         macro 재생할 MacroData. events 배열]] - `uses` [INFERRED]
- [[MacroEvent]] - `inherits` [EXTRACTED]
- [[MacroEvent 인스턴스를 JSON 직렬화 가능한 딕셔너리로 변환한다.]] - `uses` [INFERRED]
- [[MacroFlow JSON 직렬화·역직렬화 및 편집 유틸리티.  저장 시 .bak 파일 자동 생성. 로드 시 스키마 버전 마이그레이션 수행. r]] - `uses` [INFERRED]
- [[MacroFlow 재생 엔진.  절대 타임스탬프 기준 재생과 드리프트 보정을 구현한다. clickdrag 판별은 settings 임계값으로 재]] - `uses` [INFERRED]
- [[PlaybackError]] - `uses` [INFERRED]
- [[Run the GUI smoke test and return the structured status payload.]] - `uses` [INFERRED]
- [[UI 입력을 저장값으로 변환한다 -1=녹화 타이밍, 0 이상=재생 전 대기.]] - `uses` [INFERRED]
- [[Windows RDP GUI smoke harness for MacroFlow.  This script is intentionally a man]] - `uses` [INFERRED]
- [[_DisplayRow]] - `uses` [INFERRED]
- [[_PlayState]] - `uses` [INFERRED]
- [[_dict_to_event()]] - `calls` [INFERRED]
- [[build_smoke_macro()]] - `calls` [INFERRED]
- [[events 리스트를 표시용 _DisplayRow 리스트로 변환한다.      연속된 mouse_down+up → 클릭드래그 한 행으로 그룹화]] - `uses` [INFERRED]
- [[events를 raw_events 전체 복사본으로 되돌린다 (is_edited=False).      Args         macro 원본]] - `uses` [INFERRED]
- [[events에서 mouse_move 이벤트를 모두 제거한다. raw_events는 유지.      Args         macro 원본 M]] - `uses` [INFERRED]
- [[events에서 특정 id의 KeyEvent key·vk_code를 수정한다.      Args         macro 원본 MacroDa]] - `uses` [INFERRED]
- [[events에서 특정 id의 MouseWheelEvent delta를 수정한다.      Args         macro 원본 MacroD]] - `uses` [INFERRED]
- [[events에서 특정 id의 delay_override_ms만 수정한다.      Args         macro 원본 MacroData.]] - `uses` [INFERRED]
- [[events에서 특정 id의 mouse_down 이벤트의 color_check_enabled를 토글한다.      Args         ma]] - `uses` [INFERRED]
- [[events에서 특정 id의 마우스 이벤트 좌표를 수정한다.      Args         macro 원본 MacroData.]] - `uses` [INFERRED]
- [[events에서 특정 mouse_down 이벤트의 color_check_on_mismatch를 변경한다.      Args         ma]] - `uses` [INFERRED]
- [[test_simple_event_rows_keep_labels_details_and_truncation_contract()]] - `calls` [INFERRED]
- [[types.py]] - `contains` [EXTRACTED]
- [[window_trigger 이벤트 — 창 제목 감지 대기.      Attributes         window_title_contains]] - `rationale_for` [EXTRACTED]
- [[그룹 행 비고는 primary event(mouse_downkey_down 등)의 remark를 표시한다.]] - `uses` [INFERRED]
- [[단일 이벤트를 실행한다.      Args         event 실행할 이벤트.         settings clickdrag 판별]] - `uses` [INFERRED]
- [[대상 events의 재생 대기를 동일 값 또는 녹화 타이밍(None)으로 설정한다.      Args         macro 원본 Macr]] - `uses` [INFERRED]
- [[딕셔너리를 AnyEvent 서브클래스 인스턴스로 변환한다.      Args         d JSON에서 파싱된 이벤트 딕셔너리.]] - `uses` [INFERRED]
- [[목표 픽셀 색이 나타날 때까지 폴링한다.      마우스를 해당 위치로 먼저 이동한다. hover로 색이 변하는 UI 요소     (버튼 활성화]] - `uses` [INFERRED]
- [[비고가 있어도 내용detail과 색상 swatch 메타데이터는 별도로 유지한다.]] - `uses` [INFERRED]
- [[색 대기 중 hover 갱신을 위해 1px 이동 후 원위치하고 다음 시각을 반환한다.]] - `uses` [INFERRED]
- [[색 체크 wait 모드 지정 픽셀 색이 일치할 때까지 폴링한다.      타임아웃 시 경고 로그만 남기고 클릭을 계속 진행한다 (skip과 달]] - `uses` [INFERRED]
- [[색 체크 클릭의 skipstopwait 모드는 row kindlabeldetailcolor_hex에 고정된다.]] - `uses` [INFERRED]
- [[색 체크가 꺼진 클릭의 recorded_color는 수동 swatch 메타데이터로만 보존된다.]] - `uses` [INFERRED]
- [[색 체크가 켜진 드래그 row도 refresh 중 emoji 초기화 오류 없이 표시되어야 한다.]] - `uses` [INFERRED]
- [[색 트리거 row는 target_color 표시와 timeout_ms=0 무제한 대기 의미를 보존한다.]] - `uses` [INFERRED]
- [[선택된 재생 구간에서 실행 완료된 이벤트 비율을 반환한다 (0.0~1.0).]] - `uses` [INFERRED]
- [[숨겨진 mouse_move는 row 목록에서 빠지지만 다음 row의 상대시간 기준을 흐리면 안 된다.]] - `uses` [INFERRED]
- [[실제 색과 목표 색의 각 채널 차이가 tolerance 이내인지 확인한다.]] - `uses` [INFERRED]
- [[실제 재생을 수행하는 스레드 함수.      core-beliefs.md 원칙 3 절대 타임스탬프 기준 + 드리프트 보정.      Args]] - `uses` [INFERRED]
- [[여러 MacroData를 타임스탬프 오프셋을 적용하여 하나로 병합한다.      각 매크로 사이에 gap_ms 간격을 두고, source_fil]] - `uses` [INFERRED]
- [[외부 JSON 숫자를 안전한 runtime 범위로 정규화한다.]] - `uses` [INFERRED]
- [[위치 편집 대상 kind 정책은 드래그고아 클릭표시된 이동을 포함하고 대기 행은 제외한다.]] - `uses` [INFERRED]
- [[이벤트 에디터 표시 row 순수 로직 회귀 테스트.]] - `uses` [INFERRED]
- [[이벤트 자체 대기 시간 때문에 이후 timestamp가 따라잡혀 버리지 않도록 보정값을 반환한다.]] - `uses` [INFERRED]
- [[재생 중 클릭드래그 판별에 사용하는 상태.]] - `uses` [INFERRED]
- [[재생 중단을 요청하고 내부 대기를 깨운 뒤 worker 종료를 기다린다.]] - `uses` [INFERRED]
- [[저장값을 UI 입력으로 변환한다. legacy 음수 override는 즉시(0)로 표시한다.]] - `uses` [INFERRED]
- [[저장된 settings 딕셔너리를 MacroSettings로 변환한다.      기존 파일에는 클릭 색 체크 timeout이 `color_che]] - `uses` [INFERRED]
- [[지정 제목을 포함한 창이 나타날 때까지 폴링한다.      Raises         PlaybackError on_timeout==err]] - `uses` [INFERRED]
- [[클릭 색 체크 mismatch action에 대응하는 timeout(ms)을 반환한다.]] - `uses` [INFERRED]
- [[클릭 색 체크 action별 설정 시간 동안 목표 색이 나타나는지 폴링한다.      Returns         목표 색이 timeout]] - `uses` [INFERRED]
- [[키 downup pairing과 미소비 key_up row 표시는 handler 분리 후에도 보존한다.]] - `uses` [INFERRED]
- [[텍스트대기창조건반복 row의 labeldetail 계약을 고정한다.]] - `uses` [INFERRED]
- [[필요 시 스키마 버전을 현재 버전으로 마이그레이션한다.]] - `uses` [INFERRED]
- [[현재 재생 중인 이벤트의 원본 인덱스를 반환한다.]] - `uses` [INFERRED]
- [[휠 row는 같은 축의 연속 이벤트만 합산하고 다른 축에서 그룹을 끊는다.]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MacroSettings