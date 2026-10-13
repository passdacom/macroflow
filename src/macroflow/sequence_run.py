"""One owner for immutable whole-flow cycles, gaps, pause and stop.

Run options are session-only and never alter the saved graph.
"""
from __future__ import annotations

import copy
import threading
from collections.abc import Callable
from pathlib import Path

from macroflow.flow_clock import FlowClock
from macroflow.macro_file import load
from macroflow.script_engine import FlowEngine, MacroFlow, MacroNode
from macroflow.types import MacroData


class SequenceRunSession:
    def __init__(self, flow_path: str, *, repeat_count: int | None = 1,
                 interval_ms: int = 1000, speed: float = 1.0,
                 on_node_start: Callable[[str, str], None] | None = None,
                 on_node_done: Callable[[str, bool, str], None] | None = None,
                 on_complete: Callable[[str], None] | None = None,
                 on_error: Callable[[str], None] | None = None,
                 on_cycle: Callable[[int], None] | None = None) -> None:
        if repeat_count is not None and (type(repeat_count) is not int or repeat_count < 1):
            raise ValueError("반복 횟수는 1 이상이어야 합니다.")
        if type(interval_ms) is not int or interval_ms < 0:
            raise ValueError("회차 간격은 0 이상이어야 합니다.")
        self.path = flow_path
        self.total = repeat_count
        self.interval_ms = interval_ms
        self.speed = speed
        self.on_node_start = on_node_start
        self.on_node_done = on_node_done
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_cycle = on_cycle
        self._stop = threading.Event()
        self._clock = FlowClock(self._stop)
        self._gate = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_thread: threading.Thread | None = None
        self._engine: FlowEngine | None = None
        self.cycle = 0
        self._used = False
        self._terminal_error: str | None = None

    def start(self, flow: MacroFlow) -> None:
        with self._gate:
            if self._used or self._stop.is_set():
                raise RuntimeError("실행 세션은 재사용할 수 없습니다.")
            snapshot = copy.deepcopy(flow)
            if not snapshot.nodes or not snapshot.start_node_id:
                raise ValueError("빈 플로우는 실행할 수 없습니다.")
            base = Path(self.path).parent.resolve()
            cache: dict[Path, MacroData] = {}
            macros: dict[str, MacroData] = {}
            for node in snapshot.nodes.values():
                if isinstance(node, MacroNode):
                    raw = Path(node.macro_path)
                    path = raw.resolve() if raw.is_absolute() else (base / raw).resolve()
                    if (not raw.is_absolute() and not path.is_relative_to(base)) or path.suffix.lower() != ".json":
                        raise ValueError("허용되지 않은 매크로 경로입니다.")
                    if path not in cache:
                        cache[path] = load(str(path))
                    macros[node.id] = copy.deepcopy(cache[path])
            self._used = True
            self._thread = threading.Thread(target=self._run, args=(snapshot, macros),
                                            daemon=True, name="SequenceRunSession")
            self._thread.start()

    def _run(self, flow: MacroFlow, macros: dict[str, MacroData]) -> None:
        try:
            while self.total is None or self.cycle < self.total:
                if not self._clock.wait():
                    return
                result: list[str] = []
                errors: list[str] = []
                with self._gate:
                    if self._stop.is_set():
                        return
                    engine = FlowEngine(self.path, speed=self.speed,
                        on_node_start=self.on_node_start, on_node_done=self.on_node_done,
                        on_complete=result.append, on_error=errors.append,
                        macro_snapshots=macros)
                    self._engine = engine
                    if self._clock.paused:
                        engine.pause()
                    self.cycle += 1
                    if self.on_cycle:
                        self.on_cycle(self.cycle)
                    if self._stop.is_set():
                        return
                    engine.start(copy.deepcopy(flow))
                # A terminal callback is not worker exit. Retain ownership until joined.
                engine.join()
                with self._gate:
                    self._engine = None
                # Cleanup failures are terminal even for an explicitly stopped run.
                if errors:
                    raise RuntimeError(errors[0])
                if self._stop.is_set():
                    return
                if result != ["success"]:
                    raise RuntimeError("플로우가 성공 종료되지 않았습니다.")
                if self.total is not None and self.cycle >= self.total:
                    break
                # Cooperative yield for empty/zero-gap infinite runs; bounded thread count.
                if not self._clock.wait(max(.001, self.interval_ms / 1000)):
                    return
            if self.on_complete and not self._stop.is_set():
                self.on_complete("success")
        except Exception as exc:
            with self._gate:
                self._terminal_error = str(exc)
            if self.on_error:
                self.on_error(str(exc))

    @property
    def terminal_error(self) -> str | None:
        """Retain failure independently of queued GUI callback delivery."""
        with self._gate:
            return self._terminal_error

    def pause(self) -> None:
        with self._gate:
            self._clock.pause()
            if self._engine is not None:
                self._engine.pause()

    def resume(self) -> None:
        with self._gate:
            if self._engine is not None:
                self._engine.resume()
            self._clock.resume()

    def pause_state(self) -> str:
        with self._gate:
            if not self._clock.paused:
                return "running"
            return self._engine.pause_state() if self._engine is not None else "paused"

    def stop(self) -> None:
        with self._gate:
            self._stop.set()
            self._clock.wake()
            engine = self._engine
        if engine is not None:
            engine.stop()
        self.join(5)

    def request_stop(self) -> None:
        """Close the start gate now, reap workers without blocking the GUI."""
        with self._gate:
            self._stop.set()
            self._clock.wake()
            if self._stop_thread is not None and self._stop_thread.is_alive():
                return
            self._stop_thread = threading.Thread(target=self.stop, daemon=True,
                                                 name="SequenceStop")
            self._stop_thread.start()

    def join(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)

    def is_running(self) -> bool:
        return any(thread is not None and thread.is_alive()
                   for thread in (self._thread, self._stop_thread))
