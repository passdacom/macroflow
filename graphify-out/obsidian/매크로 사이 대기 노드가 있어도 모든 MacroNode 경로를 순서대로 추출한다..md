---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_sequencer_backlog.py"
type: "rationale"
community: "MacroSequencerWidget FlowEngine EndNode MacroFlow"
location: "L27"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_FlowEngine_EndNode_MacroFlow
---

# 매크로 사이 대기 노드가 있어도 모든 MacroNode 경로를 순서대로 추출한다.

## Connections
- [[EndNode]] - `uses` [INFERRED]
- [[MacroFlow]] - `uses` [INFERRED]
- [[MacroNode]] - `uses` [INFERRED]
- [[WaitFixedNode]] - `uses` [INFERRED]
- [[test_linear_macro_paths_walks_through_wait_nodes()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_FlowEngine_EndNode_MacroFlow