---
type: community
cohesion: 0.09
members: 30
---

# test expression sandbox module.py

**Cohesion:** 0.09 - loosely connected
**Members:** 30 nodes

## Members
- [[ConditionEvent를 샌드박스 내에서 평가하고 분기를 실행한다.      DSL 표현식에서 허용하는 함수         pixel_co]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py
- [[Expression sandbox resource-safety regression tests.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[Pure expression-sandbox module boundaries and compatibility contracts.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[Pure validation rules for MacroFlow condition expressions.  This module owns the]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[Return whether an AST node is statically a numeric expression.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[Validate a sandbox wait value and return milliseconds as a float.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[Validate that an expression contains only the permitted AST surface.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[_condition()]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[_is_numeric_expression()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[_validate_expression()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py
- [[execute_condition()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py
- [[expression_sandbox.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[test_condition_enforces_cumulative_wait_budget()]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[test_condition_wait_is_interrupted_by_stop_signal()]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[test_expression_keeps_numeric_multiplication_available()]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[test_expression_rejects_literal_wait_over_budget()]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[test_expression_rejects_sequence_multiplication_amplification()]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[test_expression_sandbox_imports_without_script_engine_or_pyqt()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_expression_sandbox_keeps_numeric_modulo_available()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_expression_sandbox_module.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_expression_sandbox_public_validator_preserves_security_rules()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_expression_sandbox_rejects_escape_and_oversized_inputs()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_expression_sandbox_rejects_invalid_wait_values()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_expression_sandbox_rejects_string_modulo_amplification()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_script_engine_preserves_legacy_validation_names()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[test_script_engine_security.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_script_engine_security.py
- [[test_script_engine_validation_alias_honors_runtime_wait_limit()]] - code - /root/.openclaw/workspace/macroflow/tests/test_expression_sandbox_module.py
- [[validate_expression()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[validate_wait_ms()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/expression_sandbox.py
- [[현재 runtime wait 상한으로 expression sandbox 규칙을 검증한다.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/script_engine.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_expression_sandbox_module.py
SORT file.name ASC
```

## Connections to other communities
- 10 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 2 edges to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 1 edge to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]
- 1 edge to [[_COMMUNITY_execute event PlayState test]]

## Top bridge nodes
- [[execute_condition()]] - degree 5, connects to 2 communities
- [[_validate_expression()]] - degree 7, connects to 1 community
- [[_condition()]] - degree 4, connects to 1 community
- [[test_condition_enforces_cumulative_wait_budget()]] - degree 4, connects to 1 community
- [[현재 runtime wait 상한으로 expression sandbox 규칙을 검증한다.]] - degree 3, connects to 1 community