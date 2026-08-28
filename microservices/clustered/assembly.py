"""Dependency-clustered campus process.

Faculty, student, grade, finance, and attendance stay in one process (in-process
ASGI peers) because Locust overview/enrollment/GPA/attendance join them at
request time. Library stays a separate HTTP service (weak dashboard coupling).

This is not the historical six-service gold materialization.
"""

from __future__ import annotations

import os
from typing import Any

from attendance.main import create_app as attendance_app
from common.db import make_engine
from common.http import Peers
from common.peers import set_peers
from faculty.api import internal as faculty_internal
from faculty.main import create_app as faculty_app
from finance.main import create_app as finance_app
from gateway.main import create_app as gateway_app
from grade.main import create_app as grade_app
from identity.main import create_app as identity_app
from library.main import create_app as library_app
from student.api import internal as student_internal
from student.main import create_app as student_app

DB_ENV = {
    "identity": "SEMS_IDENTITY_DATABASE_URL",
    "faculty": "SEMS_FACULTY_DATABASE_URL",
    "student": "SEMS_STUDENT_DATABASE_URL",
    "grade": "SEMS_GRADE_DATABASE_URL",
    "finance": "SEMS_FINANCE_DATABASE_URL",
    "attendance": "SEMS_ATTENDANCE_DATABASE_URL",
    "library": "SEMS_LIBRARY_DATABASE_URL",
}


def create_campus_app(
    engines: dict[str, Any] | None = None,
    library_url: str | None = None,
    include_library_app: bool = False,
):
    resolved = engines or _engines_from_env()
    identity = identity_app(resolved["identity"])
    apps = {
        "identity": identity,
        "faculty": faculty_app(resolved["faculty"]),
        "student": student_app(resolved["student"]),
        "grade": grade_app(resolved["grade"]),
        "finance": finance_app(resolved["finance"]),
        "attendance": attendance_app(resolved["attendance"]),
    }
    urls: dict[str, str] = {}
    if library_url and not include_library_app:
        urls["library"] = library_url.rstrip("/")
    else:
        library_engine = resolved.get("library")
        if library_engine is None:
            raise RuntimeError("in-process library needs a library engine")
        apps["library"] = library_app(library_engine)
    peers = Peers(apps=apps, urls=urls or None)
    set_peers(peers)
    gateway = gateway_app(peers=peers, identity_engine=resolved["identity"])
    # Library talks to campus over HTTP for identity/student/faculty internals.
    gateway.include_router(student_internal)
    gateway.include_router(faculty_internal)
    return gateway


def _engines_from_env() -> dict[str, Any]:
    engines = {}
    fallback = os.environ.get("SEMS_DATABASE_URL")
    for name, env_name in DB_ENV.items():
        url = os.environ.get(env_name) or fallback
        if not url:
            continue
        engines[name] = make_engine(url)
    if "identity" not in engines:
        raise RuntimeError("campus process needs SEMS_IDENTITY_DATABASE_URL or SEMS_DATABASE_URL")
    return engines
