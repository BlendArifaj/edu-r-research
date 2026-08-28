from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

from app.deps import request_id_ctx
from app.instrumentation.context import begin_trace, current_trace, reset_trace
from app.instrumentation.resources import rss_bytes_if_available, sample_rusage
from app.instrumentation.store import get_store

_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/favicon.ico")
_SKIP_EXACT = {"/health"}


def _should_skip(path: str) -> bool:
    if path in _SKIP_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in _SKIP_PREFIXES)


class RequestContextMiddleware:
    """ASGI middleware that records measured request traces (not fabricated)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        if _should_skip(path):
            await self.app(scope, receive, send)
            return

        header_map = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        request_id = header_map.get("x-request-id") or str(uuid4())
        request_id_ctx.set(request_id)
        begin_trace(method, path, request_id=request_id)
        started = perf_counter()
        cpu_user_0, cpu_sys_0, _ = sample_rusage()
        status_holder = {"code": 500}

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = int(message.get("status", 500))
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                duration_ms = (perf_counter() - started) * 1000
                headers.append((b"x-response-time-ms", f"{duration_ms:.2f}".encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            trace = current_trace()
            if trace is not None:
                trace.exception = exc.__class__.__name__
            raise
        finally:
            trace = current_trace()
            if trace is not None:
                cpu_user_1, cpu_sys_1, _ = sample_rusage()
                trace.duration_ms = (perf_counter() - started) * 1000
                trace.status_code = status_holder["code"]
                trace.cpu_user_delta_s = round(cpu_user_1 - cpu_user_0, 6)
                trace.cpu_system_delta_s = round(cpu_sys_1 - cpu_sys_0, 6)
                trace.rss_bytes = rss_bytes_if_available()
                get_store().record(trace)
            reset_trace()
