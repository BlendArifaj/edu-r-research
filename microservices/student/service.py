from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, DomainError
from app.schemas import (
    EnrollmentIn,
    SemesterRegistrationIn,
    StudentIn,
    StudentOut,
    StudentOverviewOut,
    StudentUpdate,
)
from common.http import Peers
from student.models import (
    CourseEnrollment,
    SemesterRegistration,
    Student,
    enrollment_pair,
    faculty_student_count,
    is_enrolled,
    is_registered,
    registration_pair,
    require_student,
    student_by_user,
)


class StudentService:
    def __init__(self, db: Session, peers: Peers) -> None:
        self.db = db
        self.peers = peers

    def create_student(self, data: StudentIn) -> Student:
        self.peers.call("faculty", "GET", f"/internal/faculties/{data.faculty_id}")
        self.peers.call("faculty", "GET", f"/internal/departments/{data.department_id}")
        user = self.peers.call(
            "identity",
            "POST",
            "/internal/users",
            json={
                "email": data.email,
                "password": data.password,
                "full_name": data.full_name,
                "role": "student",
            },
        )
        student = Student(
            user_id=int(user["id"]),
            student_number=data.student_number,
            faculty_id=data.faculty_id,
            department_id=data.department_id,
            enrollment_year=data.enrollment_year,
            status="active",
        )
        self.db.add(student)
        self.db.flush()
        self.peers.call(
            "finance",
            "POST",
            f"/internal/accounts/{student.id}",
            json={"faculty_id": student.faculty_id},
        )
        return student

    def list_students(self, faculty_id: int | None = None) -> list[Student]:
        stmt = select(Student)
        if faculty_id is not None:
            stmt = stmt.where(Student.faculty_id == faculty_id)
        return list(self.db.scalars(stmt))

    def get_student(self, student_id: int) -> Student:
        return require_student(self.db, student_id)

    def update_student(self, student_id: int, data: StudentUpdate) -> Student:
        student = self.get_student(student_id)
        payload = data.model_dump(exclude_unset=True)
        if "full_name" in payload and payload["full_name"]:
            self.peers.call(
                "identity",
                "PATCH",
                f"/internal/users/{student.user_id}",
                json={"full_name": payload.pop("full_name")},
            )
        if payload.get("department_id") is not None:
            self.peers.call("faculty", "GET", f"/internal/departments/{payload['department_id']}")
        for key, value in payload.items():
            setattr(student, key, value)
        self.db.flush()
        return student

    def register_semester(self, student_id: int, data: SemesterRegistrationIn) -> SemesterRegistration:
        student = self.get_student(student_id)
        if student.status != "active":
            raise DomainError("inactive students cannot register")
        self.peers.call("faculty", "GET", f"/internal/semesters/{data.semester_id}")
        if registration_pair(self.db, student_id, data.semester_id):
            raise ConflictError("already registered for this semester")
        self._assert_no_hold(student_id)
        row = SemesterRegistration(
            student_id=student_id,
            semester_id=data.semester_id,
            status="registered",
            registered_at=datetime.now(UTC),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_registrations(self, student_id: int) -> list[SemesterRegistration]:
        self.get_student(student_id)
        return list(
            self.db.scalars(
                select(SemesterRegistration).where(SemesterRegistration.student_id == student_id)
            )
        )

    def enroll(self, student_id: int, data: EnrollmentIn) -> CourseEnrollment:
        student = self.get_student(student_id)
        course = self.peers.call("faculty", "GET", f"/internal/courses/{data.course_id}")
        if student.status != "active":
            raise DomainError("inactive students cannot enroll")
        if enrollment_pair(self.db, student_id, int(course["id"])):
            raise ConflictError("already enrolled in this course")
        if not is_registered(self.db, student_id, int(course["semester_id"])):
            raise DomainError("semester registration required before enrollment")
        self._assert_no_hold(student_id)
        row = CourseEnrollment(
            student_id=student_id,
            course_id=int(course["id"]),
            semester_id=int(course["semester_id"]),
            status="enrolled",
            enrolled_at=datetime.now(UTC),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_enrollments(self, student_id: int) -> list[CourseEnrollment]:
        self.get_student(student_id)
        return list(
            self.db.scalars(select(CourseEnrollment).where(CourseEnrollment.student_id == student_id))
        )

    def list_student_courses(self, student_id: int) -> list[dict]:
        courses = []
        for row in self.list_enrollments(student_id):
            courses.append(self.peers.call("faculty", "GET", f"/api/v1/courses/{row.course_id}"))
        return courses

    def overview(self, student_id: int) -> StudentOverviewOut:
        student = self.get_student(student_id)
        gpa = self.peers.call("grade", "GET", f"/api/v1/students/{student_id}/gpa")
        account = self.peers.call("finance", "GET", f"/api/v1/students/{student_id}/account")
        attendance = self.peers.call("attendance", "GET", f"/internal/present-rate/{student_id}")
        loans = self.peers.call("library", "GET", "/internal/loans/count", params={"user_id": student.user_id})
        return StudentOverviewOut(
            student=StudentOut.model_validate(student),
            gpa=Decimal(str(gpa["gpa"])),
            account_balance=Decimal(str(account["balance"])),
            attendance_rate=Decimal(str(attendance["rate"])),
            active_loans=int(loans["count"]),
            enrolled_courses=len(self.list_enrollments(student_id)),
        )

    def enrolled(self, student_id: int, course_id: int) -> bool:
        self.get_student(student_id)
        return is_enrolled(self.db, student_id, course_id)

    def count_for_faculty(self, faculty_id: int) -> int:
        return faculty_student_count(self.db, faculty_id)

    def by_user(self, user_id: int) -> Student | None:
        return student_by_user(self.db, user_id)

    def _assert_no_hold(self, student_id: int) -> None:
        hold = self.peers.call("finance", "GET", f"/internal/holds/{student_id}")
        if hold.get("outstanding"):
            raise DomainError("outstanding balance must be cleared before registration")
