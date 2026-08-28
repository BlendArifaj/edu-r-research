from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import EnrollmentStatus, RegistrationStatus, StudentStatus


class Student(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "students"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    student_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False, index=True
    )
    enrollment_year: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=StudentStatus.ACTIVE, nullable=False)

    user: Mapped["User"] = relationship(back_populates="student")
    faculty: Mapped["Faculty"] = relationship(back_populates="students")
    department: Mapped["Department"] = relationship(back_populates="students")
    semester_registrations: Mapped[list["SemesterRegistration"]] = relationship(
        back_populates="student"
    )
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(back_populates="student")
    account: Mapped["StudentAccount | None"] = relationship(back_populates="student", uselist=False)


class SemesterRegistration(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semester_registrations"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=RegistrationStatus.REGISTERED, nullable=False
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    student: Mapped[Student] = relationship(back_populates="semester_registrations")
    semester: Mapped["Semester"] = relationship()

    __table_args__ = (
        UniqueConstraint("student_id", "semester_id", name="uq_semester_registration"),
    )


class CourseEnrollment(PrimaryKeyMixin, TimestampMixin, Base):
    """Owned by Student in the reference architecture; read by Grade and Attendance."""

    __tablename__ = "course_enrollments"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=EnrollmentStatus.ENROLLED, nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    student: Mapped[Student] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
    semester: Mapped["Semester"] = relationship()

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_course_enrollment"),)
