from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin
from app.models.enums import ExamType


class Exam(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exams"

    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    exam_type: Mapped[str] = mapped_column(String(32), default=ExamType.FINAL, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=100)

    course: Mapped["Course"] = relationship(back_populates="exams")
    registrations: Mapped[list["ExamRegistration"]] = relationship(back_populates="exam")
    grades: Mapped[list["Grade"]] = relationship(back_populates="exam")


class ExamRegistration(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exam_registrations"

    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    exam: Mapped[Exam] = relationship(back_populates="registrations")
    student: Mapped["Student"] = relationship()

    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_exam_registration"),)


class Grade(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "grades"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    exam_id: Mapped[int | None] = mapped_column(ForeignKey("exams.id"), nullable=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    letter: Mapped[str] = mapped_column(String(4), nullable=False)
    recorded_by_teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)

    exam: Mapped[Exam | None] = relationship(back_populates="grades")
    history: Mapped[list["GradeHistory"]] = relationship(back_populates="grade")

    __table_args__ = (UniqueConstraint("student_id", "course_id", "exam_id", name="uq_grade"),)


class GradeHistory(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "grade_histories"

    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False, index=True)
    old_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    new_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    old_letter: Mapped[str] = mapped_column(String(4), nullable=False)
    new_letter: Mapped[str] = mapped_column(String(4), nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    grade: Mapped[Grade] = relationship(back_populates="history")
