import time
from collections import deque
from threading import Lock
from typing import Callable

from app.errors import AppError

MAX_TRACKED_CLIENTS = 10000


class RateLimitError(AppError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("rate_limited", f"Hiciste demasiados pedidos. Esperá {retry_after} segundos e intentá de nuevo.", 429)
        self.retry_after = retry_after


class BusyError(AppError):
    def __init__(self) -> None:
        super().__init__("busy", "Hay otro análisis en curso. Esperá a que termine e intentá de nuevo.", 429)


class SlidingWindowLimiter:
    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._limit = limit
        self._window = window
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, client: str) -> None:
        now = self._clock()
        with self._lock:
            self._forget_idle(now)
            hits = self._hits.setdefault(client, deque())
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                raise RateLimitError(max(1, int(self._window - (now - hits[0])) + 1))
            hits.append(now)

    def _forget_idle(self, now: float) -> None:
        if len(self._hits) < MAX_TRACKED_CLIENTS:
            return
        self._hits = {client: hits for client, hits in self._hits.items() if hits and now - hits[-1] < self._window}


class AnalysisGate:
    def __init__(self, slots: int) -> None:
        self._slots = slots
        self._active = 0
        self._lock = Lock()

    def __enter__(self) -> "AnalysisGate":
        with self._lock:
            if self._active >= self._slots:
                raise BusyError()
            self._active += 1
        return self

    def __exit__(self, *_) -> None:
        with self._lock:
            self._active -= 1
