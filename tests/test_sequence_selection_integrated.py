"""Partial flow uses visible rows and never includes excluded macros/gaps."""
import copy
from pathlib import Path

import pytest

from macroflow.sequence_model import InlineActionItem, MacroFileItem, WaitItem
from macroflow.types import TextInputEvent


def test_partial_mixed_exact_rows_and_no_original_changes():
    from macroflow.sequence_selection import selected_flow
    items = [MacroFileItem(step_id=f"s{i}", path=Path(f"{i}.json")) for i in range(10)]
    items[4] = WaitItem(step_id="s4", duration_ms=25)
    items[5] = InlineActionItem(step_id="s5", events=[TextInputEvent(id="w", type="text_input", timestamp_ns=0, text="synthetic")])
    before = copy.deepcopy(items)
    result = selected_flow(items, [3,4,5,6], Path("test.macroflow"), macro_gap_ms=500)
    assert result.start_node_id == "s3"
    assert set(result.nodes) == {"s3", "s4", "s5", "s6", "end_success", "end_error"}
    assert result.nodes["s6"].next_on_success == "end_success"
    assert items == before
    for selection in ([], [1,3], [-1], [10], [2,2]):
        with pytest.raises(ValueError):
            selected_flow(items, selection, Path("test.macroflow"), macro_gap_ms=500)


def test_macro_only_range_contains_only_internal_gaps():
    from macroflow.script_engine import MacroNode, WaitFixedNode
    from macroflow.sequence_selection import selected_flow
    items = [MacroFileItem(step_id=f"s{i}", path=Path(f"{i}.json")) for i in range(10)]
    result = selected_flow(items, [3,4,5,6], Path("test.macroflow"), macro_gap_ms=500)
    assert result.start_node_id == "s3"
    assert sum(isinstance(n, MacroNode) for n in result.nodes.values()) == 4
    assert sum(isinstance(n, WaitFixedNode) for n in result.nodes.values()) == 3
    assert result.nodes["s6"].next_on_success == "end_success"
    single = selected_flow(items, [3], Path("test.macroflow"), macro_gap_ms=500)
    assert not any(isinstance(n, WaitFixedNode) for n in single.nodes.values())
