---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/player.py"
type: "code"
community: "MacroData MouseButtonEvent KeyEvent MouseMoveEvent"
location: "L50"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/MacroData_MouseButtonEvent_KeyEvent_MouseMoveEvent
---

# PlaybackError

## Connections
- [[ColorTriggerEvent]] - `uses` [INFERRED]
- [[ConditionEvent]] - `uses` [INFERRED]
- [[Exception]] - `inherits` [EXTRACTED]
- [[KeyEvent]] - `uses` [INFERRED]
- [[LoopEvent]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSettings]] - `uses` [INFERRED]
- [[MouseButtonEvent]] - `uses` [INFERRED]
- [[MouseMoveEvent]] - `uses` [INFERRED]
- [[MouseWheelEvent]] - `uses` [INFERRED]
- [[TestColorCheckWait]] - `uses` [INFERRED]
- [[TestColorMatches]] - `uses` [INFERRED]
- [[TestColorTriggerInfiniteWait]] - `uses` [INFERRED]
- [[TestExecuteEvent]] - `uses` [INFERRED]
- [[TestHexToRgb]] - `uses` [INFERRED]
- [[TestPlaybackTiming]] - `uses` [INFERRED]
- [[TestTextInputPlayback]] - `uses` [INFERRED]
- [[TextInputEvent]] - `uses` [INFERRED]
- [[TextInputEvent 실행 시 send_text가 호출되어야 한다.]] - `uses` [INFERRED]
- [[WaitEvent]] - `uses` [INFERRED]
- [[WindowTriggerEvent]] - `uses` [INFERRED]
- [[_execute_event()]] - `calls` [EXTRACTED]
- [[_wait_for_color()]] - `calls` [EXTRACTED]
- [[_wait_for_window()]] - `calls` [EXTRACTED]
- [[delay_override_ms가 설정된 이벤트는 그 딜레이만큼 기다려야 한다.]] - `uses` [INFERRED]
- [[play()가 완료 콜백을 호출해야 한다.]] - `uses` [INFERRED]
- [[player.py]] - `contains` [EXTRACTED]
- [[skip 모드는 설정 시간 동안 기다린 뒤에도 안 맞을 때만 클릭을 건너뛴다.]] - `uses` [INFERRED]
- [[stop 모드는 설정 시간 이후에도 색이 안 맞으면 재생을 중단한다.]] - `uses` [INFERRED]
- [[stop 모드도 설정 시간 동안 색 변화를 기다리고, 맞으면 클릭을 진행한다.]] - `uses` [INFERRED]
- [[stop() 호출 후 재생이 중단되어야 한다.]] - `uses` [INFERRED]
- [[timeout_ms=0 색 트리거는 타임아웃 없이 색이 나올 때까지 대기해야 한다.]] - `uses` [INFERRED]
- [[wait 모드 픽셀 색이 일치할 때까지 폴링 후 클릭이 진행되어야 한다.]] - `uses` [INFERRED]
- [[독립 색 트리거 대기 중에도 1초 이후 hover 갱신용 미세 이동을 수행한다.]] - `uses` [INFERRED]
- [[빈 문자열 TextInputEvent는 send_text를 호출하지 않아야 한다.]] - `uses` [INFERRED]
- [[색 체크 대기 1초 이후에는 hover 갱신을 위해 커서를 미세 이동 후 복귀한다.]] - `uses` [INFERRED]
- [[절대 타임스탬프 기준 재생 및 드리프트 보정 테스트.      core-beliefs.md 원칙 3 검증.]] - `uses` [INFERRED]
- [[클릭 색 체크 timeout_ms=0은 색이 나올 때까지 무제한 대기한다.]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/MacroData_MouseButtonEvent_KeyEvent_MouseMoveEvent