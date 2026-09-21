"""All authored event attributes and timing survive internal buffer roundtrip."""
import copy
import dataclasses

import pytest

from macroflow.event_fragments import copy_fragment, paste_fragment
from macroflow.macro_file import load, save
from macroflow.types import ColorTriggerEvent, MouseButtonEvent, MouseMoveEvent, TextInputEvent
from tests.test_merge_input_boundaries import macro


def test_full_fields_timing_and_save_load(tmp_path):
    events = [
        TextInputEvent(id="prefix", type="text_input", timestamp_ns=0, text="synthetic"),
        MouseButtonEvent(id="down", type="mouse_down", timestamp_ns=10_000_000,
            x_ratio=.1, y_ratio=.2, button="right", recorded_color="#123456",
            color_check_enabled=True, color_check_on_mismatch="wait", delay_override_ms=-10,
            source_file="synthetic", remark="preserve"),
        MouseMoveEvent(id="move", type="mouse_move", timestamp_ns=20_000_000,
            x_ratio=.3, y_ratio=.4, delay_override_ms=0),
        MouseButtonEvent(id="up", type="mouse_up", timestamp_ns=30_000_000,
            x_ratio=.5, y_ratio=.6, button="right"),
        ColorTriggerEvent(id="color", type="color_trigger", timestamp_ns=40_000_000,
            x_ratio=.7, y_ratio=.8, target_color="#ABCDEF", tolerance=7,
            timeout_ms=125, check_interval_ms=3, on_timeout="skip", delay_override_ms=100),
    ]
    before = copy.deepcopy(events)
    packet = copy_fragment(events, 1, 5)
    result = paste_fragment(events, events, packet, len(events))
    assert events == before
    assert len({e.id for e in result}) == len(result)
    assert result[5].timestamp_ns == 50_000_000
    for old, new in zip(events[1:], result[5:], strict=True):
        expected = dataclasses.replace(old, id=new.id, timestamp_ns=old.timestamp_ns+40_000_000)
        assert new == expected
    document = macro(events)
    document.events = result
    save(document, str(tmp_path / "fragment.json"))
    assert load(str(tmp_path / "fragment.json")) == document
    with pytest.raises(ValueError):
        paste_fragment(events, events, packet, 2)
    assert events == before
