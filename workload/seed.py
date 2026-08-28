#!/usr/bin/env python3
"""Deterministic SEMS-R seed. Synthetic data, not production SEMS records."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "monolith"))

from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal, create_schema, reset_schema  # noqa: E402
from app.models import (  # noqa: E402
    AcademicYear,
    Book,
    BookCopy,
    Course,
    Department,
    Faculty,
    Fee,
    Semester,
    Staff,
    Teacher,
    User,
)
from app.models.enums import UserRole  # noqa: E402
from app.schemas import (  # noqa: E402
    ClassSessionIn,
    EnrollmentIn,
    ExamIn,
    FeeIn,
    GradeIn,
    InvoiceIn,
    LibraryMemberIn,
    LoanIn,
    PaymentIn,
    SemesterRegistrationIn,
    StudentAttendanceIn,
    StudentIn,
)
from app.security import hash_password  # noqa: E402
from app.services import (  # noqa: E402
    AttendanceService,
    FinanceService,
    GradeService,
    LibraryService,
    StudentService,
)

DEFAULT_PASSWORD = "password123"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed SEMS-R synthetic data")
    parser.add_argument("--scale", choices=["tiny", "small"], default="tiny")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--reset",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Drop and recreate tables before seeding (default: true). Re-running seed is safe.",
    )
    return parser.parse_args()


def scale_counts(scale: str) -> dict[str, int]:
    if scale == "small":
        return {"students": 40, "courses": 8, "books": 12}
    return {"students": 8, "courses": 3, "books": 4}


def seed(db: Session, counts: dict[str, int]) -> None:
    admin = User(
        email="admin@sems-r.local",
        password_hash=hash_password("admin123"),
        full_name="SEMS-R Administrator",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    faculty = Faculty(code="ENG", name="Faculty of Engineering", established_year=1971)
    db.add(faculty)
    db.flush()
    department = Department(faculty_id=faculty.id, code="CS", name="Computer Science")
    db.add(department)
    db.flush()

    staff_user = User(
        email="teacher@sems-r.local",
        password_hash=hash_password(DEFAULT_PASSWORD),
        full_name="Ada Teacher",
        role=UserRole.TEACHER,
    )
    db.add(staff_user)
    db.flush()
    staff = Staff(
        user_id=staff_user.id,
        faculty_id=faculty.id,
        department_id=department.id,
        staff_number="STF-ENG-0001",
        position="lecturer",
        employment_type="full_time",
    )
    db.add(staff)
    db.flush()
    teacher = Teacher(staff_id=staff.id, academic_title="Dr", specialization="software architecture")
    db.add(teacher)

    year = AcademicYear(
        name="2026/27",
        start_date=date(2026, 10, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db.add(year)
    db.flush()
    semester = Semester(
        academic_year_id=year.id,
        name="Winter",
        term_number=1,
        start_date=date(2026, 10, 1),
        end_date=date(2027, 2, 15),
    )
    db.add(semester)
    db.flush()

    courses: list[Course] = []
    for index in range(counts["courses"]):
        course = Course(
            code=f"CS{100 + index}",
            name=f"Course {index + 1}",
            faculty_id=faculty.id,
            department_id=department.id,
            teacher_id=teacher.id,
            semester_id=semester.id,
            credits=6,
        )
        db.add(course)
        courses.append(course)
    db.flush()

    students_svc = StudentService(db)
    finance = FinanceService(db)
    grades = GradeService(db)
    attendance = AttendanceService(db)
    library = LibraryService(db)

    fee = finance.create_fee(
        FeeIn(name="Tuition", amount=Decimal("250.00"), fee_type="tuition", faculty_id=faculty.id)
    )

    for index in range(counts["students"]):
        student = students_svc.create_student(
            StudentIn(
                email=f"student{index + 1}@sems-r.local",
                password=DEFAULT_PASSWORD,
                full_name=f"Student {index + 1}",
                student_number=f"2026{index + 1:05d}",
                faculty_id=faculty.id,
                department_id=department.id,
                enrollment_year=2026,
            )
        )
        invoice = finance.create_invoice(
            InvoiceIn(student_id=student.id, semester_id=semester.id, fee_ids=[fee.id])
        )
        finance.record_payment(PaymentIn(invoice_id=invoice.id, amount=Decimal("250.00"), method="bank"))
        students_svc.register_semester(student.id, SemesterRegistrationIn(semester_id=semester.id))
        course = courses[index % len(courses)]
        students_svc.enroll(student.id, EnrollmentIn(course_id=course.id))
        exam = grades.create_exam(
            ExamIn(
                course_id=course.id,
                semester_id=semester.id,
                exam_type="final",
                scheduled_at=datetime.now(UTC),
                max_score=Decimal("100"),
            )
        )
        grades.register_for_exam(exam.id, student.id)
        grades.record_grade(
            GradeIn(
                student_id=student.id,
                course_id=course.id,
                exam_id=exam.id,
                semester_id=semester.id,
                score=Decimal("70") + Decimal(index % 20),
                recorded_by_teacher_id=teacher.id,
            )
        )
        session = attendance.create_session(
            ClassSessionIn(
                course_id=course.id,
                teacher_id=teacher.id,
                semester_id=semester.id,
                scheduled_at=datetime.now(UTC) - timedelta(days=1),
                topic="Lecture",
            )
        )
        attendance.record_student_attendance(
            session.id, StudentAttendanceIn(student_id=student.id, status="present")
        )

    for index in range(counts["books"]):
        book = Book(
            isbn=f"978000000{index:04d}",
            title=f"Textbook {index + 1}",
            author="SEMS-R Reconstruction",
            publisher="Experimental Press",
            year=2020 + (index % 5),
        )
        db.add(book)
        db.flush()
        copy = BookCopy(book_id=book.id, barcode=f"BC-{index + 1:04d}", location="main")
        db.add(copy)
        db.flush()
        if index == 0:
            first_student = students_svc.list_students()[0]
            member = library.create_member(
                LibraryMemberIn(
                    user_id=first_student.user_id,
                    member_type="student",
                    member_number="LIB-STU-00001",
                )
            )
            library.borrow(LoanIn(copy_id=copy.id, member_id=member.id, days=14))

    db.commit()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("SEMS_SEED", str(args.seed))
    if args.reset:
        reset_schema()
    else:
        create_schema()
    db = SessionLocal()
    try:
        seed(db, scale_counts(args.scale))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(
        f"Seeded SEMS-R synthetic {args.scale} dataset (seed={args.seed}, reset={args.reset}). "
        "This is reconstructed experimental data, not production SEMS records."
    )


if __name__ == "__main__":
    main()
