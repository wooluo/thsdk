# encoding: utf-8
from __future__ import annotations

import threading
import time
from typing import Any, Callable

from thsdk import THS


class THSConnectionError(RuntimeError):
    def __init__(self, payload: dict[str, Any]):
        super().__init__(str(payload.get("error", "THS 连接失败")))
        self.payload = payload


class THSSingletonConnection:
    """Serialize queries through one shared THS client and keep the TCP session alive."""

    def __init__(self, ths_factory: Callable[[], Any] = THS):
        self._ths_factory = ths_factory
        self._ths: Any | None = None
        self._lock = threading.RLock()

    def execute(self, query: Callable[[Any], Any]) -> Any:
        wait_started_at = time.perf_counter()
        with self._lock:
            lock_wait_ms = round((time.perf_counter() - wait_started_at) * 1000, 2)
            raw_payload, request_view, timing = self._execute_locked(query, allow_retry=True)
            timing = dict(timing)
            timing["lock_wait_ms"] = lock_wait_ms
            return raw_payload, request_view, timing

    def close(self) -> None:
        with self._lock:
            self._reset_locked()

    def _execute_locked(self, query: Callable, allow_retry: bool) -> tuple:
        ths, connect_duration_ms = self._ensure_connected_locked()
        try:
            raw_payload, request_view, timing = query(ths)
        except Exception as exc:
            if allow_retry and _is_connection_error(str(exc)):
                self._reset_locked()
                return self._execute_locked(query, allow_retry=False)
            raise

        if allow_retry and _should_reconnect(raw_payload):
            self._reset_locked()
            return self._execute_locked(query, allow_retry=False)

        if connect_duration_ms > 0:
            timing = dict(timing)
            timing["connect_duration_ms"] = connect_duration_ms
        return raw_payload, request_view, timing

    def _ensure_connected_locked(self) -> tuple[Any, float]:
        connect_duration_ms = 0.0
        if self._ths is None:
            self._ths = self._ths_factory()

        if not getattr(self._ths, "_initialized", False):
            connect_started_at = time.perf_counter()
            connect_response = self._ths.connect()
            connect_duration_ms = round((time.perf_counter() - connect_started_at) * 1000, 2)
            if not connect_response.success:
                payload = connect_response.to_dict()
                self._reset_locked()
                raise THSConnectionError(payload)
        return self._ths, connect_duration_ms

    def _reset_locked(self) -> None:
        ths = self._ths
        self._ths = None
        if ths is None:
            return
        try:
            ths.disconnect()
        except Exception:
            pass


def _is_connection_error(message: str) -> bool:
    lowered = str(message).strip().lower()
    if not lowered:
        return False
    markers = (
        "未登录", "连接", "断开", "disconnect",
        "socket", "tcp", "broken pipe",
        "connection reset", "reset by peer",
    )
    return any(marker in lowered for marker in markers)


def _should_reconnect(raw_payload: dict[str, Any]) -> bool:
    if raw_payload.get("success", False):
        return False
    return _is_connection_error(str(raw_payload.get("error", "")))


def _response_to_dict(response) -> dict[str, Any]:
    if hasattr(response, "to_dict"):
        return response.to_dict()
    return {"success": False, "error": "invalid response", "data": None, "extra": {}}


# Global singleton
connection = THSSingletonConnection()
