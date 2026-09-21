"""Snapshot isolation and failure policy, without any native input."""
import copy

from macroflow import player
from macroflow.sequence_model import MacroFileItem
from macroflow.sequence_run import SequenceRunSession
from macroflow.sequence_selection import selected_flow
from tests.test_merge_input_boundaries import key, macro
from tests.test_sequence_run_integrated import flow


def test_selected_snapshot_never_loads_excluded_paths_and_freezes_macros(monkeypatch, tmp_path):
    import macroflow.sequence_run as runs
    source = macro([key("d", "key_down", 65, 0), key("u", "key_up", 65, 1)])
    loaded, played, errors = [], [], []
    def load(path):
        loaded.append(path)
        return source
    monkeypatch.setattr(runs, "load", load)
    def play(document, **kw):
        played.append(copy.deepcopy(document))
        kw["on_complete"]()
    monkeypatch.setattr(player, "play", play)
    items = [MacroFileItem(step_id=f"s{i}", path=tmp_path / f"{i}.json") for i in range(10)]
    original = copy.deepcopy(items)
    selected = selected_flow(items, [3,4,5,6], tmp_path / "test.macroflow", macro_gap_ms=0)
    session = SequenceRunSession(str(tmp_path / "test.macroflow"), repeat_count=2,
        interval_ms=0, on_error=errors.append,
        on_cycle=lambda n: setattr(source.events[0], "vk_code", 99))
    session.start(selected)
    session.join(2)
    assert not session.is_running() and not errors
    assert loaded == [str(tmp_path / f"{i}.json") for i in range(3,7)]
    assert len(played) == 8 and all(m.events[0].vk_code == 65 for m in played)
    assert items == original


def test_error_terminal_stops_all_repeats():
    candidate = flow()
    candidate.nodes["end"].status = "error"
    errors, cycles, complete = [], [], []
    session = SequenceRunSession("test.macroflow", repeat_count=5, interval_ms=0,
        on_error=errors.append, on_cycle=cycles.append, on_complete=complete.append)
    session.start(candidate)
    session.join(2)
    assert not session.is_running()
    assert len(errors) == 1 and cycles == [1] and complete == []
