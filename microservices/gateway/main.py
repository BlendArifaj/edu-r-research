from __future__ import annotations

import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from common.app import service_app
from common.http import Peers
from common.settings import peer_urls, service_settings
from identity.api import internal_router, public_router
from identity.deps import configure as configure_identity
from identity.models import ensure_admin

_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^/api/v1/students/\d+/grades"), "grade"),
    (re.compile(r"^/api/v1/students/\d+/gpa"), "grade"),
    (re.compile(r"^/api/v1/students/\d+/account"), "finance"),
    (re.compile(r"^/api/v1/students/\d+/invoices"), "finance"),
    (re.compile(r"^/api/v1/students/\d+/transactions"), "finance"),
    (re.compile(r"^/api/v1/students/\d+/attendance"), "attendance"),
    (re.compile(r"^/api/v1/faculties/\d+/finance-summary"), "finance"),
    (re.compile(r"^/api/v1/staff/\d+/attendance"), "attendance"),
    (re.compile(r"^/api/v1/staff-attendance"), "attendance"),
    (re.compile(r"^/api/v1/class-sessions"), "attendance"),
    (re.compile(r"^/api/v1/attendance"), "attendance"),
    (re.compile(r"^/api/v1/exams"), "grade"),
    (re.compile(r"^/api/v1/grades"), "grade"),
    (re.compile(r"^/api/v1/fees"), "finance"),
    (re.compile(r"^/api/v1/invoices"), "finance"),
    (re.compile(r"^/api/v1/payments"), "finance"),
    (re.compile(r"^/api/v1/books"), "library"),
    (re.compile(r"^/api/v1/library"), "library"),
    (re.compile(r"^/api/v1/students"), "student"),
    (re.compile(r"^/api/v1/faculties"), "faculty"),
    (re.compile(r"^/api/v1/departments"), "faculty"),
    (re.compile(r"^/api/v1/staff"), "faculty"),
    (re.compile(r"^/api/v1/teachers"), "faculty"),
    (re.compile(r"^/api/v1/courses"), "faculty"),
    (re.compile(r"^/api/v1/academic-years"), "faculty"),
    (re.compile(r"^/api/v1/semesters"), "faculty"),
]

HOP_BY_HOP = {"host", "content-length", "transfer-encoding", "connection"}


def resolve_service(path: str) -> str | None:
    for pattern, service in _RULES:
        if pattern.search(path):
            return service
    return None


def create_app(peers: Peers | None = None, identity_engine=None) -> FastAPI:
    settings = service_settings()
    _, factory = configure_identity(identity_engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if settings.bootstrap_admin:
            db = factory()
            try:
                ensure_admin(db)
            finally:
                db.close()
        yield

    app = service_app("SEMS-R API gateway", lifespan=lifespan)
    app.include_router(public_router)
    app.include_router(internal_router)
    mesh = peers if peers is not None else Peers(urls=peer_urls())

    @app.api_route("/api/v1/{full_path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
    async def proxy(full_path: str, request: Request) -> Response:
        path = f"/api/v1/{full_path}"
        service = resolve_service(path)
        if service is None:
            return JSONResponse({"detail": f"no route for {path}"}, status_code=404)
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in HOP_BY_HOP
        }
        body = await request.body()
        query = dict(request.query_params)
        response = await mesh.arequest(
            service,
            request.method,
            path,
            params=query or None,
            headers=headers,
            content=body if body else None,
        )
        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        out_headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in excluded
        }
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=out_headers,
            media_type=response.headers.get("content-type"),
        )

    return app


app = create_app()
