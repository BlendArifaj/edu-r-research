from __future__ import annotations

from typing import Any

import anyio
import httpx

from app.exceptions import AuthorizationError, ConflictError, DomainError, NotFoundError
from common.context import inbound_authorization
from common.settings import service_settings


class PeerNotFound(NotFoundError):
    """Preserve an upstream 404 detail string."""

    def __init__(self, message: str) -> None:
        DomainError.__init__(self, message)
        self.entity = "upstream"
        self.identifier = message


class Peers:
    """HTTP or in-process ASGI calls between SEMS-R services."""

    def __init__(
        self,
        urls: dict[str, str] | None = None,
        apps: dict[str, Any] | None = None,
    ) -> None:
        self._apps = dict(apps or {})
        self._urls = {name: url.rstrip("/") for name, url in (urls or {}).items()}
        self._http: httpx.Client | None = None
        if self._urls:
            keepalive = service_settings().http_keepalive
            limits = httpx.Limits(
                max_keepalive_connections=20 if keepalive else 0,
                max_connections=100,
            )
            self._http = httpx.Client(timeout=30.0, limits=limits)

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def call(
        self,
        service: str,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self.request(
            service, method, path, json=json, params=params, headers=headers
        )
        if response.status_code >= 400:
            raise_http_error(response)
        if not response.content:
            return None
        return response.json()

    def request(
        self,
        service: str,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        if service in self._apps:

            async def _go() -> httpx.Response:
                return await self.arequest(
                    service,
                    method,
                    path,
                    json=json,
                    params=params,
                    headers=headers,
                    content=content,
                )

            return anyio.run(_go)
        return self._http_request(
            service, method, path, json=json, params=params, headers=headers, content=content
        )

    async def arequest(
        self,
        service: str,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        if service in self._apps:
            return await self._asgi_request(
                service, method, path, json=json, params=params, headers=headers, content=content
            )
        return await anyio.to_thread.run_sync(
            lambda: self._http_request(
                service, method, path, json=json, params=params, headers=headers, content=content
            )
        )

    def _http_request(
        self,
        service: str,
        method: str,
        path: str,
        *,
        json: Any,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
        content: bytes | None,
    ) -> httpx.Response:
        if self._http is None:
            raise RuntimeError(f"no HTTP client configured for {service}")
        url = self._urls[service] + path
        return self._http.request(
            method, url, **_request_kwargs(json, params, headers, content)
        )

    async def _asgi_request(
        self,
        service: str,
        method: str,
        path: str,
        *,
        json: Any,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
        content: bytes | None,
    ) -> httpx.Response:
        app = self._apps[service]
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://sems-r.test",
            timeout=30.0,
        ) as client:
            return await client.request(
                method, path, **_request_kwargs(json, params, headers, content)
            )


def _request_kwargs(
    json: Any,
    params: dict[str, Any] | None,
    headers: dict[str, str] | None,
    content: bytes | None,
) -> dict[str, Any]:
    merged = dict(headers or {})
    token = inbound_authorization.get()
    if token and "authorization" not in {key.lower() for key in merged}:
        merged["Authorization"] = token
    kwargs: dict[str, Any] = {"headers": merged, "params": params}
    if content is not None:
        kwargs["content"] = content
    elif json is not None:
        kwargs["json"] = json
    return kwargs


def raise_http_error(response: httpx.Response) -> None:
    detail = _detail(response)
    status = response.status_code
    if status == 404:
        raise PeerNotFound(detail)
    if status == 409:
        raise ConflictError(detail)
    if status == 401:
        raise AuthorizationError(detail)
    raise DomainError(detail)


def _detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return response.text or f"upstream {response.status_code}"
    if isinstance(payload, dict) and payload.get("detail") is not None:
        return str(payload["detail"])
    return str(payload)
