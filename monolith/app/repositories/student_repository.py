from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import CourseEnrollment, SemesterRegistration, Student
from app.models.enums import EnrollmentStatus, RegistrationStatus


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, student_id: int) -> Student:
        student = self.db.get(Student, student_id)
        if student is None:
            raise NotFoundError("Student", student_id)
        return student

    def get_by_user_id(self, user_id: int) -> Student | None:
        return self.db.scalar(select(Student).where(Student.user_id == user_id))

    def list(self, faculty_id: int | None = None) -> list[Student]:
        stmt = select(Student)
        if faculty_id is not None:
            stmt = stmt.where(Student.faculty_id == faculty_id)
        return list(self.db.scalars(stmt.order_by(Student.id)).all())

    def add(self, student: Student) -> Student:
        self.db.add(student)
        self.db.flush()
        return student


class SemesterRegistrationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, registration_id: int) -> SemesterRegistration:
        row = self.db.get(SemesterRegistration, registration_id)
        if row is None:
            raise NotFoundError("SemesterRegistration", registration_id)
        return row

    def get_pair(self, student_id: int, semester_id: int) -> SemesterRegistration | None:
        stmt = select(SemesterRegistration).where(
            SemesterRegistration.student_id == student_id,
            SemesterRegistration.semester_id == semester_id,
        )
        return self.db.scalar(stmt)

    def list_for_student(self, student_id: int) -> list[SemesterRegistration]:
        stmt = (
            select(SemesterRegistration)
            .where(SemesterRegistration.student_id == student_id)
            .order_by(SemesterRegistration.id)
        )
        return list(self.db.scalars(stmt).all())

    def add(self, registration: SemesterRegistration) -> SemesterRegistration:
        self.db.add(registration)
        self.db.flush()
        return registration


class CourseEnrollmentRepository:
    """Student-owned enrollments; also queried directly by Grade and Attendance."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_pair(self, student_id: int, course_id: int) -> CourseEnrollment | None:
        stmt = select(CourseEnrollment).where(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.course_id == course_id,
        )
        return self.db.scalar(stmt)

    def list_for_student(self, student_id: int) -> list[CourseEnrollment]:
        stmt = (
            select(CourseEnrollment)
            .where(CourseEnrollment.student_id == student_id)
            .order_by(CourseEnrollment.id)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_course(self, course_id: int) -> list[CourseEnrollment]:
        stmt = (
            select(CourseEnrollment)
            .where(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == EnrollmentStatus.ENROLLED,
            )
            .order_by(CourseEnrollment.id)
        )
        return list(self.db.scalars(stmt).all())

    def is_enrolled(self, student_id: int, course_id: int) -> bool:
        row = self.get_pair(student_id, course_id)
        return row is not None and row.status == EnrollmentStatus.ENROLLED

    def is_registered_for_semester(self, student_id: int, semester_id: int) -> bool:
        stmt = select(SemesterRegistration).where(
            SemesterRegistration.student_id == student_id,
            SemesterRegistration.semester_id == semester_id,
            SemesterRegistration.status == RegistrationStatus.REGISTERED,
        )
        return self.db.scalar(stmt) is not None

    def add(self, enrollment: CourseEnrollment) -> CourseEnrollment:
        self.db.add(enrollment)
        self.db.flush()
        return enrollment
