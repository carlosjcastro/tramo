import time
from collections import deque
from contextlib import contextmanager
from threading import Lock
from typing import Callable, Iterator

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
    def __init__(self, slots: int, lease: float = 1800, clock: Callable[[], float] = time.monotonic) -> None:
        self._slots = slots
        self._lease = lease
        self._clock = clock
        self._tokens: list[float] = []
        self._lock = Lock()

    def acquire(self) -> float:
        with self._lock:
            now = self._clock()
            self._tokens = [token for token in self._tokens if now - token < self._lease]
            if len(self._tokens) >= self._slots:
                raise BusyError()
            self._tokens.append(now)
            return now

    def release(self, token: float) -> None:
        with self._lock:
            if token in self._tokens:
                self._tokens.remove(token)

    @contextmanager
    def hold(self) -> Iterator[None]:
        token = self.acquire()
        try:
            yield
        finally:
            self.release(token)
