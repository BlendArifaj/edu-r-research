from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.exceptions import NotFoundError
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

Base = make_base()


class CourseProjection(TimestampMixin, Base):
    """Local copy of faculty-owned course fields needed for GPA and averages."""

    __tablename__ = "course_projections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)


class Exam(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exams"

    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    exam_type: Mapped[str] = mapped_column(String(32), default="final", nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=100)


class ExamRegistration(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exam_registrations"

    exam_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_exam_registration"),)


class Grade(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "grades"

    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    exam_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    letter: Mapped[str] = mapped_column(String(4), nullable=False)
    recorded_by_teacher_id: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "course_id", "exam_id", name="uq_grade"),)


class GradeHistory(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "grade_histories"

    grade_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    old_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    new_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    old_letter: Mapped[str] = mapped_column(String(4), nullable=False)
    new_letter: Mapped[str] = mapped_column(String(4), nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def require_exam(db: Session, exam_id: int) -> Exam:
    row = db.get(Exam, exam_id)
    if row is None:
        raise NotFoundError("Exam", exam_id)
    return row


def require_grade(db: Session, grade_id: int) -> Grade:
    row = db.get(Grade, grade_id)
    if row is None:
        raise NotFoundError("Grade", grade_id)
    return row


def faculty_average(db: Session, faculty_id: int) -> Decimal:
    value = db.scalar(
        select(func.avg(Grade.score))
        .join(CourseProjection, CourseProjection.id == Grade.course_id)
        .where(CourseProjection.faculty_id == faculty_id)
    )
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))
