from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.exceptions import NotFoundError
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

Base = make_base()


class Student(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "students"

    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    student_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    enrollment_year: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class SemesterRegistration(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semester_registrations"

    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="registered", nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "semester_id", name="uq_semester_registration"),)


class CourseEnrollment(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "course_enrollments"

    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="enrolled", nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_course_enrollment"),)


def require_student(db: Session, student_id: int) -> Student:
    row = db.get(Student, student_id)
    if row is None:
        raise NotFoundError("Student", student_id)
    return row


def student_by_user(db: Session, user_id: int) -> Student | None:
    return db.scalar(select(Student).where(Student.user_id == user_id))


def registration_pair(db: Session, student_id: int, semester_id: int) -> SemesterRegistration | None:
    return db.scalar(
        select(SemesterRegistration).where(
            SemesterRegistration.student_id == student_id,
            SemesterRegistration.semester_id == semester_id,
        )
    )


def enrollment_pair(db: Session, student_id: int, course_id: int) -> CourseEnrollment | None:
    return db.scalar(
        select(CourseEnrollment).where(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.course_id == course_id,
        )
    )


def is_registered(db: Session, student_id: int, semester_id: int) -> bool:
    return registration_pair(db, student_id, semester_id) is not None


def is_enrolled(db: Session, student_id: int, course_id: int) -> bool:
    row = enrollment_pair(db, student_id, course_id)
    return row is not None and row.status == "enrolled"


def faculty_student_count(db: Session, faculty_id: int) -> int:
    value = db.scalar(select(func.count()).select_from(Student).where(Student.faculty_id == faculty_id))
    return int(value or 0)
