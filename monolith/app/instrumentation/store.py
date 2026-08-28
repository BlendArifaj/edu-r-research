from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from threading import Lock

from app.instrumentation.context import RequestTrace


class TraceStore:
    """In-memory ring buffer plus optional JSONL sink. Never invents rows."""

    def __init__(self, maxlen: int = 20_000) -> None:
        self._lock = Lock()
        self._items: deque[dict[str, object]] = deque(maxlen=maxlen)
        self._path: Path | None = None

    def configure(self, path: str | None) -> None:
        self._path = Path(path) if path else None
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, trace: RequestTrace) -> None:
        payload = trace.to_dict()
        with self._lock:
            self._items.append(payload)
            if self._path is not None:
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload) + "\n")

    def snapshot(self, limit: int | None = None) -> list[dict[str, object]]:
        with self._lock:
            rows = list(self._items)
        if limit is not None:
            return rows[-limit:]
        return rows

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def summary(self) -> dict[str, object]:
        rows = self.snapshot()
        by_endpoint: dict[str, int] = {}
        sql_total = 0
        for row in rows:
            endpoint = str(row.get("endpoint", ""))
            by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1
            sql_total += int(row.get("sql_query_count") or 0)
        return {
            "trace_count": len(rows),
            "sql_query_total": sql_total,
            "by_endpoint": by_endpoint,
            "integrity": "sems-r-reconstruction-measured",
        }


_STORE = TraceStore()


def get_store() -> TraceStore:
    return _STORE
