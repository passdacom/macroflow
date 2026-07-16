---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py"
type: "code"
community: "EndNode MacroFlow FlowEngine MacroNode"
location: "L339"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/EndNode_MacroFlow_FlowEngine_MacroNode
---

# FlowEngine

## Connections
- [[.__init__()]] - `method` [EXTRACTED]
- [[._execute_node()]] - `method` [EXTRACTED]
- [[._run()]] - `method` [EXTRACTED]
- [[._run_color_check_node()]] - `method` [EXTRACTED]
- [[._run_counter_node()]] - `method` [EXTRACTED]
- [[._run_macro_node()]] - `method` [EXTRACTED]
- [[.is_running()]] - `method` [EXTRACTED]
- [[.run_sequence()]] - `calls` [INFERRED]
- [[.start()]] - `method` [EXTRACTED]
- [[.stop()]] - `method` [EXTRACTED]
- [[ConditionEvent]] - `uses` [INFERRED]
- [[End-to-end regressions discovered by the 2026-07 functional audit.]] - `uses` [INFERRED]
- [[FlowEngine lifecycle and terminal-callback regression tests.]] - `uses` [INFERRED]
- [[LoopEvent]] - `uses` [INFERRED]
- [[MacroFlow 플로우차트 시퀀서 위젯.  두 가지 모드를 제공한다 1. 단순 모드 — 매크로 JSON 파일을 순서대로 드래그앤드롭, 순차]] - `uses` [INFERRED]
- [[MacroFlow 플로우차트 실행 엔진.      .macroflow 파일을 노드 그래프로 순회하며 실행한다.     각 매크로 노드는 play]] - `rationale_for` [EXTRACTED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[_MacroItem]] - `uses` [INFERRED]
- [[macro_000 형식 node_id를 _items 인덱스로 변환한다.]] - `uses` [INFERRED]
- [[script_engine.py]] - `contains` [EXTRACTED]
- [[test_flow_color_check_clamps_non_positive_poll_interval()]] - `calls` [INFERRED]
- [[test_flow_color_check_timeout_zero_waits_until_match()]] - `calls` [INFERRED]
- [[test_flow_color_timeout_rejects_match_after_deadline()]] - `calls` [INFERRED]
- [[test_missing_macro_reports_node_failure_once()]] - `calls` [INFERRED]
- [[test_stop_interrupts_color_check_poll_without_callback()]] - `calls` [INFERRED]
- [[test_stop_interrupts_fixed_wait_without_success_callback()]] - `calls` [INFERRED]
- [[worker가 종료 확인되기 전까지 active run으로 간주한다.]] - `uses` [INFERRED]
- [[내부 드래그앤드롭 재정렬 후 _items 순서를 동기화한다.]] - `uses` [INFERRED]
- [[단순 선형 플로우의 균일한 매크로 사이 대기값을 반환한다.      대기가 없으면 0, 분기지원하지 않는 노드서로 다른 대기값이면 None이]] - `uses` [INFERRED]
- [[매크로 시퀀서 위젯.      QListWidget 기반 드래그앤드롭 정렬 + 실행 상태 표시.     매크로 JSON 파일을 목록에 추가하여]] - `uses` [INFERRED]
- [[목록 항목 더블클릭 시 해당 매크로를 에디터로 불러온다.]] - `uses` [INFERRED]
- [[목록이 있는 시퀀스의 대기값 변경을 미저장 변경으로 기록한다.]] - `uses` [INFERRED]
- [[미저장 변경의 저장·폐기·취소를 확인한다.          Returns             열기 또는 종료를 계속해도 되면 True. 저장]] - `uses` [INFERRED]
- [[미저장 상태를 변경하고 실제 전이만 알린다.]] - `uses` [INFERRED]
- [[시퀀서의 모든 매크로를 하나로 병합하여 에디터에 전달한다.          각 매크로 파일을 순서대로 로드하고, macro_file.merge_]] - `uses` [INFERRED]
- [[외부(main_window)에서 시퀀스를 시작한다.]] - `uses` [INFERRED]
- [[외부(main_window)에서 현재 플로우를 다른 이름으로 저장한다.]] - `uses` [INFERRED]
- [[외부(main_window)에서 현재 플로우를 저장한다.]] - `uses` [INFERRED]
- [[외부에서 매크로 파일을 시퀀서에 추가한다.]] - `uses` [INFERRED]
- [[저장되지 않은 시퀀서 변경이 있는지 반환한다.]] - `uses` [INFERRED]
- [[중지를 요청하고 worker 종료가 확인됐는지 반환한다.]] - `uses` [INFERRED]
- [[파일 다이얼로그 초기 폴더를 반환한다.]] - `uses` [INFERRED]
- [[플로우를 단순 시퀀서로 손실 없이 투영한다.      성공 경로는 ``Macro (Wait Macro) End`` 형태여야 하며, 모든 대]] - `uses` [INFERRED]
- [[현재 목록에서 선형 MacroFlow를 생성한다.          gap_ms  0 이면 매크로 노드 사이에 WaitFixedNode를 삽입한]] - `uses` [INFERRED]
- [[현재 시퀀스의 매크로 단계 수를 반환한다.]] - `uses` [INFERRED]
- [[호환용 callback 현재 generation을 포함해 GUI thread로 전달한다.]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/EndNode_MacroFlow_FlowEngine_MacroNode