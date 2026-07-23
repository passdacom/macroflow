"""Win32 foreground-window helper contract tests."""

from __future__ import annotations

from macroflow.win32.window import _activate_with_user32


class _FakeFunction:
    def __init__(self, name: str, calls: list[tuple[object, ...]], result: int = 1) -> None:
        self._name = name
        self._calls = calls
        self._result = result

    def __call__(self, *args: object) -> int:
        self._calls.append((self._name, *args))
        return self._result


class _FakeUser32:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.ShowWindow = _FakeFunction("ShowWindow", self.calls)
        self.SetWindowPos = _FakeFunction("SetWindowPos", self.calls)
        self.SetForegroundWindow = _FakeFunction("SetForegroundWindow", self.calls)


def test_activate_with_user32_shows_and_transiently_raises_window() -> None:
    user32 = _FakeUser32()

    assert _activate_with_user32(user32, 1234)
    assert user32.calls == [
        ("ShowWindow", 1234, 5),
        ("SetWindowPos", 1234, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040),
        ("SetWindowPos", 1234, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040),
        ("SetForegroundWindow", 1234),
    ]


def test_activate_with_user32_rejects_invalid_handle() -> None:
    user32 = _FakeUser32()

    assert not _activate_with_user32(user32, 0)
    assert user32.calls == []
