from datetime import UTC, datetime

from fastapi.testclient import TestClient


def _bootstrap_academic_graph(client: TestClient, headers: dict[str, str]) -> dict[str, int]:
    faculty = client.post(
        "/api/v1/faculties",
        json={"code": "ENG", "name": "Engineering", "established_year": 1970},
        headers=headers,
    )
    assert faculty.status_code == 201, faculty.text
    faculty_id = faculty.json()["id"]

    department = client.post(
        "/api/v1/departments",
        json={"faculty_id": faculty_id, "code": "CS", "name": "Computer Science"},
        headers=headers,
    )
    assert department.status_code == 201, department.text
    department_id = department.json()["id"]

    staff = client.post(
        "/api/v1/staff",
        json={
            "email": "teacher@sems-r.local",
            "password": "teach123",
            "full_name": "Ada Teacher",
            "faculty_id": faculty_id,
            "department_id": department_id,
            "staff_number": "STF-ENG-0001",
            "position": "lecturer",
            "employment_type": "full_time",
        },
        headers=headers,
    )
    assert staff.status_code == 201, staff.text
    staff_id = staff.json()["id"]

    teacher = client.post(
        "/api/v1/teachers",
        json={"staff_id": staff_id, "academic_title": "Dr", "specialization": "databases"},
        headers=headers,
    )
    assert teacher.status_code == 201, teacher.text
    teacher_id = teacher.json()["id"]

    year = client.post(
        "/api/v1/academic-years",
        json={
            "name": "2026/27",
            "start_date": "2026-10-01",
            "end_date": "2027-06-30",
            "is_current": True,
        },
        headers=headers,
    )
    assert year.status_code == 201, year.text
    year_id = year.json()["id"]

    semester = client.post(
        "/api/v1/semesters",
        json={
            "academic_year_id": year_id,
            "name": "Winter",
            "term_number": 1,
            "start_date": "2026-10-01",
            "end_date": "2027-02-15",
        },
        headers=headers,
    )
    assert semester.status_code == 201, semester.text
    semester_id = semester.json()["id"]

    course = client.post(
        "/api/v1/courses",
        json={
            "code": "CS101",
            "name": "Intro to Programming",
            "faculty_id": faculty_id,
            "department_id": department_id,
            "teacher_id": teacher_id,
            "semester_id": semester_id,
            "credits": 6,
        },
        headers=headers,
    )
    assert course.status_code == 201, course.text

    student = client.post(
        "/api/v1/students",
        json={
            "email": "student@sems-r.local",
            "password": "stud1234",
            "full_name": "Nora Student",
            "student_number": "202600001",
            "faculty_id": faculty_id,
            "department_id": department_id,
            "enrollment_year": 2026,
        },
        headers=headers,
    )
    assert student.status_code == 201, student.text

    return {
        "faculty_id": faculty_id,
        "department_id": department_id,
        "staff_id": staff_id,
        "teacher_id": teacher_id,
        "semester_id": semester_id,
        "course_id": course.json()["id"],
        "student_id": student.json()["id"],
        "user_id": student.json()["user_id"],
    }


def test_faculty_and_course_administration(client: TestClient, auth_headers: dict[str, str]) -> None:
    ids = _bootstrap_academic_graph(client, auth_headers)
    listing = client.get("/api/v1/courses", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()[0]["code"] == "CS101"
    stats = client.get(f"/api/v1/faculties/{ids['faculty_id']}/statistics", headers=auth_headers)
    assert stats.status_code == 200
    assert stats.json()["students"] == 1
    assert stats.json()["courses"] == 1


def test_enrollment_requires_semester_registration(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    ids = _bootstrap_academic_graph(client, auth_headers)
    blocked = client.post(
        f"/api/v1/students/{ids['student_id']}/enrollments",
        json={"course_id": ids["course_id"]},
        headers=auth_headers,
    )
    assert blocked.status_code == 400

    registered = client.post(
        f"/api/v1/students/{ids['student_id']}/semester-registrations",
        json={"semester_id": ids["semester_id"]},
        headers=auth_headers,
    )
    assert registered.status_code == 201, registered.text

    enrolled = client.post(
        f"/api/v1/students/{ids['student_id']}/enrollments",
        json={"course_id": ids["course_id"]},
        headers=auth_headers,
    )
    assert enrolled.status_code == 201, enrolled.text


def test_finance_hold_blocks_registration(client: TestClient, auth_headers: dict[str, str]) -> None:
    ids = _bootstrap_academic_graph(client, auth_headers)
    fee = client.post(
        "/api/v1/fees",
        json={"name": "Tuition", "amount": "100.00", "fee_type": "tuition"},
        headers=auth_headers,
    )
    assert fee.status_code == 201, fee.text
    invoice = client.post(
        "/api/v1/invoices",
        json={
            "student_id": ids["student_id"],
            "semester_id": ids["semester_id"],
            "fee_ids": [fee.json()["id"]],
        },
        headers=auth_headers,
    )
    assert invoice.status_code == 201, invoice.text

    blocked = client.post(
        f"/api/v1/students/{ids['student_id']}/semester-registrations",
        json={"semester_id": ids["semester_id"]},
        headers=auth_headers,
    )
    assert blocked.status_code == 400

    payment = client.post(
        "/api/v1/payments",
        json={"invoice_id": invoice.json()["id"], "amount": "100.00", "method": "bank"},
        headers=auth_headers,
    )
    assert payment.status_code == 201, payment.text

    allowed = client.post(
        f"/api/v1/students/{ids['student_id']}/semester-registrations",
        json={"semester_id": ids["semester_id"]},
        headers=auth_headers,
    )
    assert allowed.status_code == 201, allowed.text

    account = client.get(f"/api/v1/students/{ids['student_id']}/account", headers=auth_headers)
    assert account.json()["balance"] == "0.00"


def test_grade_attendance_library_and_overview(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    ids = _bootstrap_academic_graph(client, auth_headers)
    client.post(
        f"/api/v1/students/{ids['student_id']}/semester-registrations",
        json={"semester_id": ids["semester_id"]},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/students/{ids['student_id']}/enrollments",
        json={"course_id": ids["course_id"]},
        headers=auth_headers,
    )

    exam = client.post(
        "/api/v1/exams",
        json={
            "course_id": ids["course_id"],
            "semester_id": ids["semester_id"],
            "exam_type": "final",
            "scheduled_at": datetime.now(UTC).isoformat(),
            "max_score": "100",
        },
        headers=auth_headers,
    )
    assert exam.status_code == 201, exam.text
    exam_id = exam.json()["id"]

    unenrolled_grade = client.post(
        "/api/v1/grades",
        json={
            "student_id": ids["student_id"],
            "course_id": ids["course_id"],
            "exam_id": exam_id,
            "semester_id": ids["semester_id"],
            "score": "88",
            "recorded_by_teacher_id": 999,
        },
        headers=auth_headers,
    )
    assert unenrolled_grade.status_code == 404

    grade = client.post(
        "/api/v1/grades",
        json={
            "student_id": ids["student_id"],
            "course_id": ids["course_id"],
            "exam_id": exam_id,
            "semester_id": ids["semester_id"],
            "score": "88",
            "recorded_by_teacher_id": ids["teacher_id"],
        },
        headers=auth_headers,
    )
    assert grade.status_code == 201, grade.text
    assert grade.json()["letter"] == "B"

    gpa = client.get(f"/api/v1/students/{ids['student_id']}/gpa", headers=auth_headers)
    assert gpa.status_code == 200
    assert gpa.json()["gpa"] == "3.00"

    session = client.post(
        "/api/v1/class-sessions",
        json={
            "course_id": ids["course_id"],
            "teacher_id": ids["teacher_id"],
            "semester_id": ids["semester_id"],
            "scheduled_at": datetime.now(UTC).isoformat(),
            "topic": "Recursion",
        },
        headers=auth_headers,
    )
    assert session.status_code == 201, session.text
    attendance = client.post(
        f"/api/v1/class-sessions/{session.json()['id']}/attendance",
        json={"student_id": ids["student_id"], "status": "present"},
        headers=auth_headers,
    )
    assert attendance.status_code == 201, attendance.text

    book = client.post(
        "/api/v1/books",
        json={
            "isbn": "9780000000001",
            "title": "Distributed Systems",
            "author": "Tanenbaum",
            "publisher": "Pearson",
            "year": 2017,
        },
        headers=auth_headers,
    )
    assert book.status_code == 201, book.text
    copy = client.post(
        f"/api/v1/books/{book.json()['id']}/copies",
        json={"barcode": "BC-1", "location": "main"},
        headers=auth_headers,
    )
    assert copy.status_code == 201, copy.text
    member = client.post(
        "/api/v1/library/members",
        json={
            "user_id": ids["user_id"],
            "member_type": "student",
            "member_number": "LIB-STU-00001",
        },
        headers=auth_headers,
    )
    assert member.status_code == 201, member.text
    loan = client.post(
        "/api/v1/library/loans",
        json={"copy_id": copy.json()["id"], "member_id": member.json()["id"], "days": 14},
        headers=auth_headers,
    )
    assert loan.status_code == 201, loan.text

    overview = client.get(f"/api/v1/students/{ids['student_id']}/overview", headers=auth_headers)
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["gpa"] == "3.00"
    assert body["active_loans"] == 1
    assert body["enrolled_courses"] == 1
    assert body["attendance_rate"] == "1.00"
