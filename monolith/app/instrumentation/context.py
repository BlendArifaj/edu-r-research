from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class RequestTrace:
    """One measured HTTP request. Values are recorded at runtime, not synthesized."""

    request_id: str
    method: str
    path: str
    endpoint: str
    timestamp: str
    duration_ms: float = 0.0
    status_code: int = 0
    components: list[str] = field(default_factory=list)
    database_entities: list[str] = field(default_factory=list)
    sql_query_count: int = 0
    sql_preview: list[str] = field(default_factory=list)
    exception: str | None = None
    rss_bytes: int | None = None
    cpu_user_delta_s: float | None = None
    cpu_system_delta_s: float | None = None
    integrity: str = "sems-r-reconstruction-measured"

    _component_set: set[str] = field(default_factory=set, repr=False)
    _entity_set: set[str] = field(default_factory=set, repr=False)

    def touch_component(self, name: str) -> None:
        if name and name not in self._component_set:
            self._component_set.add(name)
            self.components.append(name)

    def touch_entity(self, name: str) -> None:
        if name and name not in self._entity_set:
            self._entity_set.add(name)
            self.database_entities.append(name)

    def add_sql(self, statement: str) -> None:
        self.sql_query_count += 1
        if len(self.sql_preview) < 20:
            compact = " ".join(statement.split())
            self.sql_preview.append(compact[:500])

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp,
            "duration_ms": round(self.duration_ms, 3),
            "status_code": self.status_code,
            "components": list(self.components),
            "database_entities": list(self.database_entities),
            "sql_query_count": self.sql_query_count,
            "sql_preview": list(self.sql_preview),
            "exception": self.exception,
            "rss_bytes": self.rss_bytes,
            "cpu_user_delta_s": self.cpu_user_delta_s,
            "cpu_system_delta_s": self.cpu_system_delta_s,
            "integrity": self.integrity,
        }


_trace_ctx: ContextVar[RequestTrace | None] = ContextVar("sems_r_trace", default=None)


def current_trace() -> RequestTrace | None:
    return _trace_ctx.get()


def begin_trace(method: str, path: str, request_id: str | None = None) -> RequestTrace:
    trace = RequestTrace(
        request_id=request_id or str(uuid4()),
        method=method.upper(),
        path=path,
        endpoint=f"{method.upper()} {path}",
        timestamp=datetime.now(UTC).isoformat(),
    )
    _trace_ctx.set(trace)
    return trace


def reset_trace() -> None:
    _trace_ctx.set(None)
