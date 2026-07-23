---
source_file: "./src/macroflow/script_engine.py"
type: "rationale"
community: "MacroSequencerWidget EndNode MacroFlow FlowEngine"
location: "L433"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine
---

# 노드를 실행하고 다음 노드 ID를 반환한다.          Returns:             다음 노드 ID. None이면 플로우 종료.

## Connections
- [[._execute_node()]] - `rationale_for` [EXTRACTED]
- [[ConditionEvent]] - `uses` [INFERRED]
- [[LoopEvent]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine