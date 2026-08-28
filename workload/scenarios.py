from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from workload.datasets import WorkloadData, pick

OK_READ = {200}
OK_CREATE = {200, 201}
OK_CREATE_OR_RACE = {200, 201, 409}


def _is_locust(client: Any) -> bool:
    return client.__class__.__name__ in {"HttpSession", "FastHttpSession"}


def response_json(response: Any) -> Any:
    if response is None:
        return None
    payload = getattr(response, "json", None)
    if not callable(payload):
        return payload
    try:
        return payload()
    except Exception:
        return None


def api(
    client: Any,
    method: str,
    path: str,
    *,
    headers: dict[str, str],
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    name: str | None = None,
    ok: set[int] | None = None,
) -> Any:
    allowed = ok or OK_READ
    if _is_locust(client):
        kw: dict[str, Any] = {"headers": headers, "name": name or path, "catch_response": True}
        if json is not None:
            kw["json"] = json
        if params is not None:
            kw["params"] = params
        with getattr(client, method)(path, **kw) as response:
            if response.status_code in allowed:
                response.success()
            else:
                response.failure(f"{response.status_code} {method.upper()} {path}")
            return response
    kwargs: dict[str, Any] = {"headers": headers}
    if json is not None:
        kwargs["json"] = json
    if params is not None:
        kwargs["params"] = params
    return getattr(client, method)(path, **kwargs)


def student_dashboard(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    student_id = pick(data.student_ids)
    api(client, "get", f"/api/v1/students/{student_id}", headers=headers, name="/api/v1/students/[id]")
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/courses",
        headers=headers,
        name="/api/v1/students/[id]/courses",
    )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/grades",
        headers=headers,
        name="/api/v1/students/[id]/grades",
    )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/account",
        headers=headers,
        name="/api/v1/students/[id]/account",
    )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/overview",
        headers=headers,
        name="/api/v1/students/[id]/overview",
    )


def grades(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    course_id = pick(data.course_ids)
    student_id = pick(data.student_ids)
    api(client, "get", "/api/v1/courses", headers=headers)
    api(
        client,
        "get",
        f"/api/v1/courses/{course_id}",
        headers=headers,
        name="/api/v1/courses/[id]",
    )
    api(client, "get", "/api/v1/exams", headers=headers, params={"course_id": course_id})
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/grades",
        headers=headers,
        name="/api/v1/students/[id]/grades",
    )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/gpa",
        headers=headers,
        name="/api/v1/students/[id]/gpa",
    )


def registration(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    """Register/enroll only when the student is not already in that state.

    A seeded student is already registered for the current semester, so a blind
    POST returns HTTP 409. That is correct API behavior, not a load-test failure.
    Locust previously marked 409 as success, which hid the conflicts in the
    Locust report while Uvicorn still logged them. We skip duplicate writes.
    """
    student_id = pick(data.student_ids)
    semester_id = pick(data.semester_ids)
    api(client, "get", "/api/v1/courses", headers=headers)
    registrations = api(
        client,
        "get",
        f"/api/v1/students/{student_id}/semester-registrations",
        headers=headers,
        name="/api/v1/students/[id]/semester-registrations",
    )
    registered = {
        int(row["semester_id"])
        for row in (response_json(registrations) or [])
        if isinstance(row, dict) and "semester_id" in row
    }
    if semester_id not in registered:
        api(
            client,
            "post",
            f"/api/v1/students/{student_id}/semester-registrations",
            headers=headers,
            json={"semester_id": semester_id},
            name="/api/v1/students/[id]/semester-registrations",
            ok=OK_CREATE_OR_RACE,
        )
    enrollments = api(
        client,
        "get",
        f"/api/v1/students/{student_id}/enrollments",
        headers=headers,
        name="/api/v1/students/[id]/enrollments",
    )
    enrolled = {
        int(row["course_id"])
        for row in (response_json(enrollments) or [])
        if isinstance(row, dict) and "course_id" in row
    }
    target_course = next((course_id for course_id in data.course_ids if course_id not in enrolled), None)
    if target_course is not None:
        api(
            client,
            "post",
            f"/api/v1/students/{student_id}/enrollments",
            headers=headers,
            json={"course_id": target_course},
            name="/api/v1/students/[id]/enrollments",
            ok=OK_CREATE_OR_RACE,
        )


def finance(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    student_id = pick(data.student_ids)
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/invoices",
        headers=headers,
        name="/api/v1/students/[id]/invoices",
    )
    if data.invoice_ids:
        api(
            client,
            "get",
            f"/api/v1/invoices/{data.invoice_ids[0]}",
            headers=headers,
            name="/api/v1/invoices/[id]",
        )
        api(
            client,
            "post",
            "/api/v1/payments",
            headers=headers,
            json={"invoice_id": data.invoice_ids[0], "amount": "0.00", "method": "bank"},
            ok=OK_CREATE_OR_RACE,
        )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/account",
        headers=headers,
        name="/api/v1/students/[id]/account",
    )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/transactions",
        headers=headers,
        name="/api/v1/students/[id]/transactions",
    )


def attendance(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    course_id = pick(data.course_ids)
    teacher_id = pick(data.teacher_ids)
    semester_id = pick(data.semester_ids)
    student_id = pick(data.student_ids)
    api(client, "get", "/api/v1/class-sessions", headers=headers, params={"course_id": course_id})
    created = api(
        client,
        "post",
        "/api/v1/class-sessions",
        headers=headers,
        json={
            "course_id": course_id,
            "teacher_id": teacher_id,
            "semester_id": semester_id,
            "scheduled_at": datetime.now(UTC).isoformat(),
            "topic": "Synthetic load-test session",
        },
        ok=OK_CREATE,
    )
    session_id = None
    body = created.json() if hasattr(created, "json") else None
    if callable(body):
        body = body()
    if isinstance(body, dict) and "id" in body:
        session_id = int(body["id"])
    elif data.session_ids:
        session_id = data.session_ids[0]
    if session_id is not None:
        api(
            client,
            "post",
            f"/api/v1/class-sessions/{session_id}/attendance",
            headers=headers,
            json={"student_id": student_id, "status": "present"},
            name="/api/v1/class-sessions/[id]/attendance",
            ok=OK_CREATE_OR_RACE,
        )
        api(
            client,
            "get",
            f"/api/v1/class-sessions/{session_id}/attendance",
            headers=headers,
            name="/api/v1/class-sessions/[id]/attendance",
        )
    api(
        client,
        "get",
        f"/api/v1/students/{student_id}/attendance",
        headers=headers,
        name="/api/v1/students/[id]/attendance",
    )


def library(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    book_id = pick(data.book_ids)
    api(client, "get", "/api/v1/books", headers=headers, params={"q": "Textbook"})
    api(client, "get", f"/api/v1/books/{book_id}", headers=headers, name="/api/v1/books/[id]")
    copies = api(
        client,
        "get",
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        name="/api/v1/books/[id]/copies",
    )
    body = copies.json() if hasattr(copies, "json") else None
    if callable(body):
        body = body()
    copy_id = None
    if isinstance(body, list) and body:
        copy_id = int(body[0]["id"])
    if copy_id is not None and data.member_ids:
        api(
            client,
            "post",
            "/api/v1/library/loans",
            headers=headers,
            json={"copy_id": copy_id, "member_id": data.member_ids[0], "days": 14},
            ok=OK_CREATE_OR_RACE,
        )
        api(
            client,
            "get",
            f"/api/v1/library/members/{data.member_ids[0]}/loans",
            headers=headers,
            name="/api/v1/library/members/[id]/loans",
        )


def faculty_admin(client: Any, headers: dict[str, str], data: WorkloadData) -> None:
    faculty_id = pick(data.faculty_ids)
    api(client, "get", "/api/v1/faculties", headers=headers)
    api(
        client,
        "get",
        f"/api/v1/faculties/{faculty_id}",
        headers=headers,
        name="/api/v1/faculties/[id]",
    )
    api(client, "get", "/api/v1/departments", headers=headers, params={"faculty_id": faculty_id})
    api(client, "get", "/api/v1/staff", headers=headers, params={"faculty_id": faculty_id})
    api(client, "get", "/api/v1/teachers", headers=headers)
    api(
        client,
        "get",
        f"/api/v1/faculties/{faculty_id}/statistics",
        headers=headers,
        name="/api/v1/faculties/[id]/statistics",
    )


JOURNEYS = {
    "student_dashboard": student_dashboard,
    "grades": grades,
    "registration": registration,
    "finance": finance,
    "attendance": attendance,
    "library": library,
    "faculty_admin": faculty_admin,
}
