from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from common.context import inbound_authorization


class ForwardAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        header = request.headers.get("authorization", "")
        token = inbound_authorization.set(header)
        try:
            return await call_next(request)
        finally:
            inbound_authorization.reset(token)
