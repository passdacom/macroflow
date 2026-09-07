"""Deterministic input-boundary probes; native SendInput is always fake."""
import ast
import ctypes
import threading
import types
from pathlib import Path

import pytest

from macroflow import player
from macroflow.types import KeyEvent, MouseButtonEvent, MouseMoveEvent, TextInputEvent
from tests.test_player_runtime_safety import _make_macro


class NativeSend:
    def __init__(self, accepted=None, cleanup_fails=False):
        self.accepted = accepted
        self.cleanup_fails = cleanup_fails
        self.calls = []
        self.held = set()

    def __call__(self, count, arr, size):
        accepted = count if self.accepted is None or self.calls else min(count, self.accepted)
        if self.calls and self.cleanup_fails:
            accepted = 0
        batch = []
        for i in range(count):
            inp = arr[i]
            if inp.type == 1:
                key = inp._input.ki
                item = ('key', key.wVk, key.dwFlags)
                if i < accepted:
                    if key.dwFlags & 2:
                        self.held.discard(key.wVk)
                    else:
                        self.held.add(key.wVk)
            else:
                item = ('mouse', inp._input.mi.dwFlags & ~0x8000)
            batch.append(item)
        self.calls.append(batch)
        return accepted


def native_module(monkeypatch, native):
    source = Path(player.__file__).parent / 'win32/sendinput.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    tree.body = [n for n in tree.body if not isinstance(n, ast.Assert)
                 and not (isinstance(n, ast.ImportFrom) and n.level)]
    module = types.ModuleType('fake_native_sendinput')
    module.get_logical_screen_size = lambda: (1920, 1080)
    monkeypatch.setattr(ctypes, 'windll', types.SimpleNamespace(
        user32=types.SimpleNamespace(SendInput=native)), raising=False)
    exec(compile(tree, str(source), 'exec'), module.__dict__)
    module._PASTE_INPUT_DRAIN_DELAY_S = 0
    return module


@pytest.fixture(autouse=True)
def reset_player():
    player.stop()
    yield
    player.stop()


def mouse(kind, ts=0, x=.1):
    return MouseButtonEvent(id=kind, type=kind, timestamp_ns=ts, x_ratio=x, y_ratio=.1)


@pytest.mark.parametrize('gate', ['execute', 'after_wait'])
@pytest.mark.parametrize('kind', ['mouse', 'move', 'key', 'text'])
@pytest.mark.parametrize('stop_waiting', [False, True])
def test_pause_after_scheduler_gate_preserves_event(monkeypatch, kind, stop_waiting, gate):
    entered, proceed, at_pause = threading.Event(), threading.Event(), threading.Event()
    calls, progress, errors = [], [], []
    original = player._execute_event
    original_wait = player._playback_clock.wait_until_resumed

    executing = threading.Event()

    def execute(event, settings, state):
        executing.set()
        if gate == "execute" and not entered.is_set():
            entered.set()
            assert proceed.wait(2)
        original(event, settings, state)

    def wait():
        if player._playback_clock.is_paused():
            at_pause.set()
        result = original_wait()
        if gate == "after_wait" and executing.is_set() and not entered.is_set():
            entered.set()
            assert proceed.wait(2)
        return result

    monkeypatch.setattr(player, '_execute_event', execute)
    monkeypatch.setattr(player._playback_clock, 'wait_until_resumed', wait)
    monkeypatch.setattr(player, 'ratio_to_pixel', lambda *a: (100, 100))
    monkeypatch.setattr(player, 'send_mouse_move', lambda *a: calls.append('move'))
    monkeypatch.setattr(player, 'send_mouse_button', lambda *a, down: calls.append(('button', down)))
    monkeypatch.setattr(player, 'send_key', lambda *a, is_down: calls.append(('key', is_down)))
    monkeypatch.setattr(player, 'set_clipboard_text', lambda *a: calls.append('clipboard') or True)
    monkeypatch.setattr(player, 'send_paste', lambda: calls.append('paste') or True)
    events = {
        'mouse': [mouse('mouse_down'), mouse('mouse_up')],
        'move': [MouseMoveEvent(id='m', type='mouse_move', timestamp_ns=0, x_ratio=.1, y_ratio=.1)],
        'key': [KeyEvent(id='d', type='key_down', timestamp_ns=0, vk_code=65, key='a'),
                KeyEvent(id='u', type='key_up', timestamp_ns=0, vk_code=65, key='a')],
        'text': [TextInputEvent(id='t', type='text_input', timestamp_ns=0, text='probe')],
    }[kind]
    player.play(_make_macro(events), on_event=lambda i, e: progress.append(i), on_error=errors.append)
    try:
        assert entered.wait(2)
        assert player.pause()
        proceed.set()
        assert at_pause.wait(.5), 'event did not wait at the input boundary'
        assert calls == []
        assert progress == []
        assert player.get_progress() == 0
        if stop_waiting:
            player.stop()
            assert calls == []
            assert progress == []
        else:
            player.resume()
            player._playback_thread.join(2)
            assert progress == list(range(len(events)))
            expected = {'mouse': ['move', ('button', True), 'move', ('button', False)],
                        'move': ['move'], 'key': [('key', True), ('key', False)],
                        'text': ['clipboard', 'paste']}[kind]
            assert calls == expected
        assert not player.is_playing()
        assert errors == []
    finally:
        proceed.set()
        player.stop()


@pytest.mark.parametrize('accepted', [0, 1, 2, 3, 4])
def test_paste_partial_delivery_releases_only_owned_keys(monkeypatch, accepted):
    native = NativeSend(accepted)
    module = native_module(monkeypatch, native)
    assert module.send_paste() is (accepted == 4)
    assert native.held == set()
    cleanup = {0: [], 1: [('key', 17, 2)], 2: [('key', 86, 2), ('key', 17, 2)],
               3: [('key', 17, 2)], 4: []}[accepted]
    assert [item for batch in native.calls[1:] for item in batch] == cleanup


def test_paste_cleanup_failure_is_bounded_and_observable(monkeypatch):
    native = NativeSend(2, cleanup_fails=True)
    module = native_module(monkeypatch, native)
    assert module.send_paste() is False
    assert 2 <= len(native.calls) <= 3
    assert all(item[2] == 2 for batch in native.calls[1:] for item in batch)


def test_partial_paste_player_reports_error_and_next_run_recovers(monkeypatch):
    native = NativeSend(2)
    module = native_module(monkeypatch, native)
    monkeypatch.setattr(player, 'send_paste', module.send_paste)
    monkeypatch.setattr(player, 'set_clipboard_text', lambda text: True)
    errors, complete = [], []
    macro = _make_macro([TextInputEvent(id='t', type='text_input', timestamp_ns=0, text='probe')])
    player.play(macro, on_error=errors.append, on_complete=lambda: complete.append(True))
    player._playback_thread.join(2)
    assert len(errors) == 1
    assert complete == []
    assert native.held == set()
    player.stop()
    player.play(macro, on_error=errors.append, on_complete=lambda: complete.append(True))
    player._playback_thread.join(2)
    assert len(errors) == 1
    assert complete == [True]


@pytest.mark.parametrize('ts,x,with_move', [(1_000_000_000, .1, False), (0, .5, False), (0, .5, True)])
def test_open_gesture_has_exactly_one_native_down_and_up(monkeypatch, ts, x, with_move):
    native = NativeSend()
    module = native_module(monkeypatch, native)
    for name in ['send_mouse_move', 'send_mouse_button', 'send_mouse_drag']:
        monkeypatch.setattr(player, name, getattr(module, name))
    events = [mouse('mouse_down')]
    if with_move:
        events.append(MouseMoveEvent(id='m', type='mouse_move', timestamp_ns=0, x_ratio=.3, y_ratio=.1))
    events.append(mouse('mouse_up', ts, x))
    errors = []
    player.play(_make_macro(events), speed=5, on_error=errors.append)
    player._playback_thread.join(2)
    assert errors == []
    flags = [item[1] for batch in native.calls for item in batch]
    assert flags.count(module.MOUSEEVENTF_LEFTDOWN) == 1
    assert flags.count(module.MOUSEEVENTF_LEFTUP) == 1


@pytest.mark.parametrize('name,args', [('send_key', (65, True)),
                                     ('send_mouse_button', (0, 0, 'left', True)),
                                     ('send_mouse_move', (0, 0)),
                                     ('send_mouse_wheel', (0, 0, 120))])
def test_single_input_rejection_is_not_silent(monkeypatch, name, args):
    native = NativeSend(0)
    module = native_module(monkeypatch, native)
    with pytest.raises(OSError, match='SendInput'):
        getattr(module, name)(*args)


@pytest.mark.parametrize('stop_waiting', [False, True])
def test_pause_during_coordinate_lookup_preserves_mouse_down(monkeypatch, stop_waiting):
    entered, proceed, waiting = threading.Event(), threading.Event(), threading.Event()
    calls, progress = [], []
    original_wait = player._playback_clock.wait_until_resumed

    def ratio(*args):
        if not entered.is_set():
            entered.set()
            assert proceed.wait(2)
        return (100, 100)

    def wait():
        if player._playback_clock.is_paused():
            waiting.set()
        return original_wait()

    monkeypatch.setattr(player, 'ratio_to_pixel', ratio)
    monkeypatch.setattr(player._playback_clock, 'wait_until_resumed', wait)
    monkeypatch.setattr(player, 'send_mouse_move', lambda *a: calls.append('move'))
    monkeypatch.setattr(player, 'send_mouse_button', lambda *a, down: calls.append(down))
    player.play(_make_macro([mouse('mouse_down'), mouse('mouse_up')]),
                on_event=lambda i, e: progress.append(i))
    try:
        assert entered.wait(2)
        assert player.pause()
        proceed.set()
        assert waiting.wait(1)
        assert calls == progress == []
        if stop_waiting:
            player.stop()
            assert calls == progress == []
        else:
            player.resume()
            player._playback_thread.join(2)
            assert calls == ['move', True, 'move', False]
            assert progress == [0, 1]
    finally:
        proceed.set()
        player.stop()


def test_mouse_pause_pending_finishes_original_release_before_pausing(monkeypatch):
    released = threading.Event()
    calls = []
    monkeypatch.setattr(player, 'ratio_to_pixel', lambda *a: (100, 100))
    monkeypatch.setattr(player, 'send_mouse_move', lambda *a: None)
    monkeypatch.setattr(player, 'send_mouse_button', lambda *a, down: calls.append(down))

    def progress(index, event):
        if index == 0:
            assert player.pause()
            assert player._pause_pending
            assert calls == [True]
        elif index == 1:
            released.set()

    player.play(_make_macro([mouse('mouse_down'), mouse('mouse_up'),
                            MouseMoveEvent(id='next', type='mouse_move', timestamp_ns=0,
                                           x_ratio=.2, y_ratio=.2)]), on_event=progress)
    assert released.wait(2)
    assert calls == [True, False]
    assert player.is_paused()
    assert player.get_progress() == 2 / 3
    player.stop()
    assert calls == [True, False]


def test_terminal_cleanup_attempts_all_releases_when_sender_raises(monkeypatch):
    state = player._PlayState(pressed_keys={17, 65}, pressed_mouse={'left': (1, 2)})
    monkeypatch.setattr(player, '_active_play_state', state)
    calls = []

    def release_key(vk, is_down):
        calls.append(vk)
        raise OSError('SendInput rejected release')

    monkeypatch.setattr(player, 'send_key', release_key)
    monkeypatch.setattr(player, 'send_mouse_button', lambda *a, **kw: calls.append('left'))
    player._release_active_inputs()
    player._release_active_inputs()
    assert sorted(calls[:2]) == [17, 65]
    assert calls[2:] == ['left']
    assert not state.pressed_keys
    assert not state.pressed_mouse
