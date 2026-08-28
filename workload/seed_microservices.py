#!/usr/bin/env python3
"""Seed the six-service reconstruction through the API gateway. Synthetic data only."""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "monolith"))

DEFAULT_PASSWORD = "password123"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed SEMS-R microservices via gateway")
    parser.add_argument("--scale", choices=["tiny", "small"], default="tiny")
    parser.add_argument("--base-url", default=os.environ.get("SEMS_BASE_URL", "http://127.0.0.1:8000"))
    return parser.parse_args()


def scale_counts(scale: str) -> dict[str, int]:
    if scale == "small":
        return {"students": 40, "courses": 8, "books": 12}
    return {"students": 8, "courses": 3, "books": 4}


def api(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    allow_conflict: bool = False,
    **kwargs: Any,
) -> httpx.Response:
    response = client.request(method, path, **kwargs)
    if response.status_code == 409 and allow_conflict:
        return response
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {response.status_code} {response.text}")
    return response


def wait_for_api(client: httpx.Client, attempts: int = 40) -> None:
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            response = client.get("/health")
            if response.status_code == 200:
                return
            last = RuntimeError(f"health HTTP {response.status_code}")
        except httpx.HTTPError as exc:
            last = exc
        time.sleep(1)
    raise RuntimeError(f"gateway not ready after {attempts}s: {last}")


def seed(client: httpx.Client, counts: dict[str, int]) -> None:
    wait_for_api(client)
    login = api(
        client,
        "POST",
        "/api/v1/auth/login",
        json={"email": "admin@sems-r.local", "password": "admin123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    faculty = api(
        client,
        "POST",
        "/api/v1/faculties",
        json={"code": "ENG", "name": "Faculty of Engineering", "established_year": 1971},
        headers=headers,
    ).json()
    department = api(
        client,
        "POST",
        "/api/v1/departments",
        json={"faculty_id": faculty["id"], "code": "CS", "name": "Computer Science"},
        headers=headers,
    ).json()
    staff = api(
        client,
        "POST",
        "/api/v1/staff",
        json={
            "email": "teacher@sems-r.local",
            "password": DEFAULT_PASSWORD,
            "full_name": "Ada Teacher",
            "faculty_id": faculty["id"],
            "department_id": department["id"],
            "staff_number": "STF-ENG-0001",
            "position": "lecturer",
            "employment_type": "full_time",
        },
        headers=headers,
    ).json()
    teacher = api(
        client,
        "POST",
        "/api/v1/teachers",
        json={"staff_id": staff["id"], "academic_title": "Dr", "specialization": "software architecture"},
        headers=headers,
    ).json()
    year = api(
        client,
        "POST",
        "/api/v1/academic-years",
        json={
            "name": "2026/27",
            "start_date": str(date(2026, 10, 1)),
            "end_date": str(date(2027, 6, 30)),
            "is_current": True,
        },
        headers=headers,
    ).json()
    semester = api(
        client,
        "POST",
        "/api/v1/semesters",
        json={
            "academic_year_id": year["id"],
            "name": "Winter",
            "term_number": 1,
            "start_date": str(date(2026, 10, 1)),
            "end_date": str(date(2027, 2, 15)),
        },
        headers=headers,
    ).json()
    courses = []
    for index in range(counts["courses"]):
        course = api(
            client,
            "POST",
            "/api/v1/courses",
            json={
                "code": f"CS{100 + index}",
                "name": f"Course {index + 1}",
                "faculty_id": faculty["id"],
                "department_id": department["id"],
                "teacher_id": teacher["id"],
                "semester_id": semester["id"],
                "credits": 6,
            },
            headers=headers,
        ).json()
        courses.append(course)
    fee = api(
        client,
        "POST",
        "/api/v1/fees",
        json={"name": "Tuition", "amount": "250.00", "fee_type": "tuition", "faculty_id": faculty["id"]},
        headers=headers,
    ).json()
    first_user_id = None
    for index in range(counts["students"]):
        student = api(
            client,
            "POST",
            "/api/v1/students",
            json={
                "email": f"student{index + 1}@sems-r.local",
                "password": DEFAULT_PASSWORD,
                "full_name": f"Student {index + 1}",
                "student_number": f"2026{index + 1:05d}",
                "faculty_id": faculty["id"],
                "department_id": department["id"],
                "enrollment_year": 2026,
            },
            headers=headers,
        ).json()
        if first_user_id is None:
            first_user_id = student["user_id"]
        invoice = api(
            client,
            "POST",
            "/api/v1/invoices",
            json={"student_id": student["id"], "semester_id": semester["id"], "fee_ids": [fee["id"]]},
            headers=headers,
        ).json()
        api(
            client,
            "POST",
            "/api/v1/payments",
            json={"invoice_id": invoice["id"], "amount": "250.00", "method": "bank"},
            headers=headers,
        )
        api(
            client,
            "POST",
            f"/api/v1/students/{student['id']}/semester-registrations",
            json={"semester_id": semester["id"]},
            headers=headers,
            allow_conflict=True,
        )
        course = courses[index % len(courses)]
        api(
            client,
            "POST",
            f"/api/v1/students/{student['id']}/enrollments",
            json={"course_id": course["id"]},
            headers=headers,
            allow_conflict=True,
        )
        exam = api(
            client,
            "POST",
            "/api/v1/exams",
            json={
                "course_id": course["id"],
                "semester_id": semester["id"],
                "exam_type": "final",
                "scheduled_at": datetime.now(UTC).isoformat(),
                "max_score": "100",
            },
            headers=headers,
        ).json()
        api(
            client,
            "POST",
            f"/api/v1/exams/{exam['id']}/registrations",
            json={"student_id": student["id"]},
            headers=headers,
            allow_conflict=True,
        )
        api(
            client,
            "POST",
            "/api/v1/grades",
            json={
                "student_id": student["id"],
                "course_id": course["id"],
                "exam_id": exam["id"],
                "semester_id": semester["id"],
                "score": str(70 + (index % 20)),
                "recorded_by_teacher_id": teacher["id"],
            },
            headers=headers,
        )
        session = api(
            client,
            "POST",
            "/api/v1/class-sessions",
            json={
                "course_id": course["id"],
                "teacher_id": teacher["id"],
                "semester_id": semester["id"],
                "scheduled_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                "topic": "Lecture",
            },
            headers=headers,
        ).json()
        api(
            client,
            "POST",
            f"/api/v1/class-sessions/{session['id']}/attendance",
            json={"student_id": student["id"], "status": "present"},
            headers=headers,
        )
    for index in range(counts["books"]):
        book = api(
            client,
            "POST",
            "/api/v1/books",
            json={
                "isbn": f"978000000{index:04d}",
                "title": f"Textbook {index + 1}",
                "author": "SEMS-R Reconstruction",
                "publisher": "Experimental Press",
                "year": 2020 + (index % 5),
            },
            headers=headers,
        ).json()
        copy = api(
            client,
            "POST",
            f"/api/v1/books/{book['id']}/copies",
            json={"barcode": f"BC-{index + 1:04d}", "location": "main"},
            headers=headers,
        ).json()
        if index == 0 and first_user_id is not None:
            member = api(
                client,
                "POST",
                "/api/v1/library/members",
                json={
                    "user_id": first_user_id,
                    "member_type": "student",
                    "member_number": "LIB-STU-00001",
                },
                headers=headers,
            ).json()
            api(
                client,
                "POST",
                "/api/v1/library/loans",
                json={"copy_id": copy["id"], "member_id": member["id"], "days": 14},
                headers=headers,
            )


def main() -> None:
    args = parse_args()
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=60.0) as client:
        seed(client, scale_counts(args.scale))
    print(
        f"Seeded SEMS-R microservices {args.scale} dataset via {args.base_url}. "
        "Reconstructed experimental data, not production SEMS records."
    )


if __name__ == "__main__":
    main()
