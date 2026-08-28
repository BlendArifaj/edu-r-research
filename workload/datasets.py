from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkloadData:
    """IDs discovered from the target API. Architecture-neutral."""

    student_ids: list[int] = field(default_factory=list)
    course_ids: list[int] = field(default_factory=list)
    faculty_ids: list[int] = field(default_factory=list)
    teacher_ids: list[int] = field(default_factory=list)
    book_ids: list[int] = field(default_factory=list)
    semester_ids: list[int] = field(default_factory=list)
    exam_ids: list[int] = field(default_factory=list)
    invoice_ids: list[int] = field(default_factory=list)
    member_ids: list[int] = field(default_factory=list)
    copy_ids: list[int] = field(default_factory=list)
    session_ids: list[int] = field(default_factory=list)
    staff_ids: list[int] = field(default_factory=list)
    user_ids_by_student: dict[int, int] = field(default_factory=dict)


def _json(response: Any) -> Any:
    if hasattr(response, "json"):
        payload = response.json()
        return payload() if callable(payload) else payload
    return None


def _ids(rows: Any, key: str = "id") -> list[int]:
    if not isinstance(rows, list):
        return []
    return [int(row[key]) for row in rows if isinstance(row, dict) and key in row]


def load_dataset(client: Any, headers: dict[str, str]) -> WorkloadData:
    data = WorkloadData()
    students = _json(client.get("/api/v1/students", headers=headers)) or []
    data.student_ids = _ids(students)
    data.user_ids_by_student = {
        int(row["id"]): int(row["user_id"])
        for row in students
        if isinstance(row, dict) and "id" in row and "user_id" in row
    }
    data.course_ids = _ids(_json(client.get("/api/v1/courses", headers=headers)) or [])
    data.faculty_ids = _ids(_json(client.get("/api/v1/faculties", headers=headers)) or [])
    data.teacher_ids = _ids(_json(client.get("/api/v1/teachers", headers=headers)) or [])
    data.book_ids = _ids(_json(client.get("/api/v1/books", headers=headers)) or [])
    data.semester_ids = _ids(_json(client.get("/api/v1/semesters", headers=headers)) or [])
    data.exam_ids = _ids(_json(client.get("/api/v1/exams", headers=headers)) or [])
    data.staff_ids = _ids(_json(client.get("/api/v1/staff", headers=headers)) or [])
    data.session_ids = _ids(_json(client.get("/api/v1/class-sessions", headers=headers)) or [])
    if data.student_ids:
        invoices = _json(
            client.get(f"/api/v1/students/{data.student_ids[0]}/invoices", headers=headers)
        )
        data.invoice_ids = _ids(invoices or [])
    if data.book_ids:
        copies = _json(
            client.get(f"/api/v1/books/{data.book_ids[0]}/copies", headers=headers)
        )
        data.copy_ids = _ids(copies or [])
    members = _json(client.get("/api/v1/library/reservations", headers=headers))
    # reservations endpoint is not a member list; discover member via first student user later
    return data


def pick(values: list[int], fallback: int = 1) -> int:
    return values[0] if values else fallback
