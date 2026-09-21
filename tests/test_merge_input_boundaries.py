"""Placement boundaries must not carry held input into the next macro."""
import copy

import pytest

from macroflow.macro_file import merge_macros
from macroflow.types import KeyEvent, MacroData, MacroMeta, MacroSettings


def macro(events):
    return MacroData(meta=MacroMeta(version="1.0", app_version="test",
        created_at="2026-09-21", screen_width=1920, screen_height=1080,
        dpi_scale=1.0), settings=MacroSettings(), raw_events=copy.deepcopy(events),
        events=events)


def key(identifier, kind, vk, time):
    return KeyEvent(id=identifier, type=kind, vk_code=vk, key=str(vk), timestamp_ns=time)


@pytest.mark.parametrize("next_vk", [27, 9])
def test_each_placement_releases_only_held_keys_before_next_action(next_vk):
    first = macro([key("ctrl", "key_down", 17, 0),
                   key("vd", "key_down", 86, 10), key("vu", "key_up", 86, 20)])
    second = macro([key("next", "key_down", next_vk, 0),
                    key("next-up", "key_up", next_vk, 10)])
    before = copy.deepcopy((first, second))
    merged = merge_macros([(first, "same"), (second, "same")], gap_ms=5)
    held = set()
    for event in merged.events:
        if event.id == "next":
            assert not held
            assert event.timestamp_ns == 5_000_020
        if event.type == "key_down":
            held.add(event.vk_code)
        elif event.type == "key_up":
            held.discard(event.vk_code)
    assert not held
    assert (first, second) == before
    assert len(merged.events) == 6


def test_repeated_placement_ids_are_unique_but_first_occurrence_preserved():
    source = macro([key("down", "key_down", 17, 0), key("up", "key_up", 17, 20)])
    merged = merge_macros([(source, "a"), (source, "a")])
    ids = [event.id for event in merged.events]
    assert len(set(ids)) == len(ids)
    assert ids[:2] == ["down", "up"]


def test_ambiguous_nested_input_and_open_button_rejected():
    from macroflow.types import LoopEvent, MouseButtonEvent
    candidates = [
        LoopEvent(id="loop", type="loop", timestamp_ns=0, count=2,
                  events=[key("child", "key_down", 17, 0)]),
        MouseButtonEvent(id="mouse", type="mouse_down", timestamp_ns=0,
                         x_ratio=0.5, y_ratio=0.5),
    ]
    for event in candidates:
        with pytest.raises(ValueError, match="플로우"):
            merge_macros([(macro([event]), "a")])


@pytest.mark.parametrize("override", [None, -10, 0, 30])
@pytest.mark.parametrize("ending", ["key", "move", "wait"])
def test_production_player_timing_and_owned_release(monkeypatch, override, ending):
    from macroflow import player
    from macroflow.types import MouseMoveEvent, WaitEvent

    events = [key("ctrl", "key_down", 17, 0),
              key("vd", "key_down", 86, 10_000_000),
              key("vu", "key_up", 86, 20_000_000)]
    if ending == "move":
        events.append(MouseMoveEvent(id="move", type="mouse_move", timestamp_ns=30_000_000,
                                     x_ratio=.1, y_ratio=.1))
    if ending == "wait":
        events.append(WaitEvent(id="wait", type="wait", timestamp_ns=30_000_000,
                                duration_ms=25))
    events[-1].delay_override_ms = override
    next_events = [key("next", "key_down", 9, 0), key("next-up", "key_up", 9, 10_000_000)]
    merged = merge_macros([(macro(events), "a"), (macro(next_events), "b")], gap_ms=50)
    unrepaired = copy.deepcopy(merged)
    unrepaired.events = [e for e in unrepaired.events if e.remark != "병합 경계에서 열린 키 해제"]

    def trace(document):
        now = [0]
        observed, held, releases = {}, set(), []
        player.stop()
        player._stop_flag.clear()
        player._playback_clock.reset()
        monkeypatch.setattr(player, "_active_now_ns", lambda: now[0])
        def wait_until(deadline):
            now[0] = max(now[0], deadline)
            return True
        monkeypatch.setattr(player._playback_clock, "wait_until", wait_until)
        monkeypatch.setattr(player, "_wait_active", lambda seconds: wait_until(now[0] + int(seconds*1e9)))
        monkeypatch.setattr(player, "ratio_to_pixel", lambda *a: (1, 1))
        monkeypatch.setattr(player, "send_mouse_move", lambda *a: None)
        def send(vk, is_down):
            if is_down:
                if vk == 9:
                    observed["held_before_next"] = set(held)
                held.add(vk)
            else:
                held.discard(vk)
                releases.append(vk)
        monkeypatch.setattr(player, "send_key", send)
        player._play_loop(document, 1.0, None, None, None, None,
                          on_event_start=lambda i, e: observed.update({e.id: now[0]}))
        assert not held
        return observed, releases

    before, _ = trace(unrepaired)
    after, releases = trace(merged)
    assert before["held_before_next"] == {17}
    assert after["held_before_next"] == set()
    assert releases.count(17) == 1
    assert {e.id: after[e.id] for e in unrepaired.events} == {
        e.id: before[e.id] for e in unrepaired.events}
