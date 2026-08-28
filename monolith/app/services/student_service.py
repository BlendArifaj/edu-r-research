from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, DomainError
from app.models import CourseEnrollment, SemesterRegistration, Student, User
from app.models.enums import EnrollmentStatus, RegistrationStatus, StudentStatus, UserRole
from app.repositories import (
    AcademicCalendarRepository,
    CourseEnrollmentRepository,
    CourseRepository,
    DepartmentRepository,
    FacultyRepository,
    SemesterRegistrationRepository,
    StudentRepository,
    UserRepository,
)
from app.schemas import EnrollmentIn, SemesterRegistrationIn, StudentIn, StudentUpdate
from app.security import hash_password
from app.services.finance_service import FinanceService


class EnrollmentGateService:
    """Blocks enrollment when finance holds exist. Student <-> Finance cycle hub."""

    def __init__(self, db: Session) -> None:
        self.finance = FinanceService(db)

    def assert_can_register(self, student_id: int) -> None:
        if self.finance.has_outstanding_balance(student_id):
            raise DomainError("outstanding balance must be cleared before registration")


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.students = StudentRepository(db)
        self.users = UserRepository(db)
        self.faculties = FacultyRepository(db)
        self.departments = DepartmentRepository(db)
        self.calendar = AcademicCalendarRepository(db)
        self.courses = CourseRepository(db)
        self.registrations = SemesterRegistrationRepository(db)
        self.enrollments = CourseEnrollmentRepository(db)
        self.gate = EnrollmentGateService(db)
        self.finance = FinanceService(db)

    def create_student(self, data: StudentIn) -> Student:
        if self.users.get_by_email(data.email):
            raise ConflictError("email already registered")
        self.faculties.get(data.faculty_id)
        self.departments.get(data.department_id)
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.STUDENT,
        )
        self.users.add(user)
        student = Student(
            user_id=user.id,
            student_number=data.student_number,
            faculty_id=data.faculty_id,
            department_id=data.department_id,
            enrollment_year=data.enrollment_year,
            status=StudentStatus.ACTIVE,
        )
        self.students.add(student)
        self.finance.ensure_account(student.id)
        return student

    def list_students(self, faculty_id: int | None = None) -> list[Student]:
        return self.students.list(faculty_id)

    def get_student(self, student_id: int) -> Student:
        return self.students.get(student_id)

    def update_student(self, student_id: int, data: StudentUpdate) -> Student:
        student = self.students.get(student_id)
        payload = data.model_dump(exclude_unset=True)
        if "full_name" in payload and payload["full_name"]:
            student.user.full_name = payload.pop("full_name")
        if "department_id" in payload and payload["department_id"] is not None:
            self.departments.get(payload["department_id"])
        for key, value in payload.items():
            setattr(student, key, value)
        self.db.flush()
        return student

    def register_semester(self, student_id: int, data: SemesterRegistrationIn) -> SemesterRegistration:
        student = self.students.get(student_id)
        if student.status != StudentStatus.ACTIVE:
            raise DomainError("inactive students cannot register")
        self.calendar.get_semester(data.semester_id)
        if self.registrations.get_pair(student_id, data.semester_id):
            raise ConflictError("already registered for this semester")
        self.gate.assert_can_register(student_id)
        registration = SemesterRegistration(
            student_id=student_id,
            semester_id=data.semester_id,
            status=RegistrationStatus.REGISTERED,
            registered_at=datetime.now(UTC),
        )
        return self.registrations.add(registration)

    def list_registrations(self, student_id: int) -> list[SemesterRegistration]:
        self.students.get(student_id)
        return self.registrations.list_for_student(student_id)

    def enroll(self, student_id: int, data: EnrollmentIn) -> CourseEnrollment:
        student = self.students.get(student_id)
        course = self.courses.get(data.course_id)
        if student.status != StudentStatus.ACTIVE:
            raise DomainError("inactive students cannot enroll")
        if self.enrollments.get_pair(student_id, course.id):
            raise ConflictError("already enrolled in this course")
        if not self.enrollments.is_registered_for_semester(student_id, course.semester_id):
            raise DomainError("semester registration required before enrollment")
        self.gate.assert_can_register(student_id)
        enrollment = CourseEnrollment(
            student_id=student_id,
            course_id=course.id,
            semester_id=course.semester_id,
            status=EnrollmentStatus.ENROLLED,
            enrolled_at=datetime.now(UTC),
        )
        return self.enrollments.add(enrollment)

    def list_enrollments(self, student_id: int) -> list[CourseEnrollment]:
        self.students.get(student_id)
        return self.enrollments.list_for_student(student_id)

    def list_student_courses(self, student_id: int):
        enrollments = self.list_enrollments(student_id)
        return [self.courses.get(row.course_id) for row in enrollments]
