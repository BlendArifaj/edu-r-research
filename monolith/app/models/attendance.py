from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import AttendanceStatus


class ClassSession(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "class_sessions"

    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)

    course: Mapped["Course"] = relationship(back_populates="class_sessions")
    attendances: Mapped[list["StudentAttendance"]] = relationship(back_populates="class_session")


class StudentAttendance(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_attendances"

    class_session_id: Mapped[int] = mapped_column(
        ForeignKey("class_sessions.id"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AttendanceStatus.PRESENT, nullable=False
    )

    class_session: Mapped[ClassSession] = relationship(back_populates="attendances")

    __table_args__ = (
        UniqueConstraint("class_session_id", "student_id", name="uq_student_attendance"),
    )


class StaffAttendance(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff_attendances"

    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False, index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=AttendanceStatus.PRESENT, nullable=False
    )

    __table_args__ = (UniqueConstraint("staff_id", "work_date", name="uq_staff_attendance"),)
