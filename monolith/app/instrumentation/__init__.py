from app.instrumentation.components import install_component_tracking
from app.instrumentation.context import current_trace
from app.instrumentation.middleware import RequestContextMiddleware
from app.instrumentation.sql import install_sql_listeners
from app.instrumentation.store import get_store


def install_runtime_instrumentation(trace_path: str | None = None) -> None:
    install_sql_listeners()
    install_component_tracking()
    get_store().configure(trace_path or None)


__all__ = [
    "RequestContextMiddleware",
    "current_trace",
    "get_store",
    "install_runtime_instrumentation",
]
