---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py"
type: "code"
community: "MacroSequencerWidget FlowEngine EndNode MacroFlow"
location: "L311"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/MacroSequencerWidget_FlowEngine_EndNode_MacroFlow
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
- [[FlowEngine 스레드에서 호출 — 목록 업데이트는 메인 스레드에서.]] - `uses` [INFERRED]
- [[LoopEvent]] - `uses` [INFERRED]
- [[MacroFlow 플로우차트 시퀀서 위젯.  두 가지 모드를 제공한다 1. 단순 모드 — 매크로 JSON 파일을 순서대로 드래그앤드롭, 순차]] - `uses` [INFERRED]
- [[MacroFlow 플로우차트 실행 엔진.      .macroflow 파일을 노드 그래프로 순회하며 실행한다.     각 매크로 노드는 play]] - `rationale_for` [EXTRACTED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[_MacroItem]] - `uses` [INFERRED]
- [[macro_000 형식 node_id를 _items 인덱스로 변환한다.]] - `uses` [INFERRED]
- [[script_engine.py]] - `contains` [EXTRACTED]
- [[내부 드래그앤드롭 재정렬 후 _items 순서를 동기화한다.]] - `uses` [INFERRED]
- [[매크로 시퀀서 위젯.      QListWidget 기반 드래그앤드롭 정렬 + 실행 상태 표시.     매크로 JSON 파일을 목록에 추가하여]] - `uses` [INFERRED]
- [[목록 항목 더블클릭 시 해당 매크로를 에디터로 불러온다.]] - `uses` [INFERRED]
- [[시퀀서의 모든 매크로를 하나로 병합하여 에디터에 전달한다.          각 매크로 파일을 순서대로 로드하고, macro_file.merge_]] - `uses` [INFERRED]
- [[외부(main_window)에서 시퀀스를 시작한다.]] - `uses` [INFERRED]
- [[외부(main_window)에서 시퀀스를 중지한다.]] - `uses` [INFERRED]
- [[외부(main_window)에서 현재 플로우를 다른 이름으로 저장한다.]] - `uses` [INFERRED]
- [[외부(main_window)에서 현재 플로우를 저장한다.]] - `uses` [INFERRED]
- [[외부에서 매크로 파일을 시퀀서에 추가한다.]] - `uses` [INFERRED]
- [[파일 다이얼로그 초기 폴더를 반환한다.]] - `uses` [INFERRED]
- [[현재 목록에서 선형 MacroFlow를 생성한다.          gap_ms  0 이면 매크로 노드 사이에 WaitFixedNode를 삽입한]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/MacroSequencerWidget_FlowEngine_EndNode_MacroFlow