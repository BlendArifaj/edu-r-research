from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.exceptions import NotFoundError
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

Base = make_base()


class ClassSession(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "class_sessions"

    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)


class StudentAttendance(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "student_attendances"

    class_session_id: Mapped[int] = mapped_column(
        ForeignKey("class_sessions.id"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="present", nullable=False)

    __table_args__ = (UniqueConstraint("class_session_id", "student_id", name="uq_student_attendance"),)


class StaffAttendance(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff_attendances"

    staff_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="present", nullable=False)

    __table_args__ = (UniqueConstraint("staff_id", "work_date", name="uq_staff_attendance"),)


def require_session(db: Session, session_id: int) -> ClassSession:
    row = db.get(ClassSession, session_id)
    if row is None:
        raise NotFoundError("ClassSession", session_id)
    return row


def present_rate(db: Session, student_id: int) -> Decimal:
    total = db.scalar(
        select(func.count())
        .select_from(StudentAttendance)
        .where(StudentAttendance.student_id == student_id)
    )
    present = db.scalar(
        select(func.count())
        .select_from(StudentAttendance)
        .where(
            StudentAttendance.student_id == student_id,
            StudentAttendance.status.in_(("present", "late")),
        )
    )
    if not total:
        return Decimal("0.00")
    return (Decimal(present or 0) / Decimal(total)).quantize(Decimal("0.01"))
