from datetime import date

from sqlalchemy import Date, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.exceptions import NotFoundError
from common.models import PrimaryKeyMixin, TimestampMixin, make_base

Base = make_base()


class Faculty(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "faculties"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    established_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dean_staff_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Department(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    head_staff_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (UniqueConstraint("faculty_id", "code", name="uq_department_faculty_code"),)


class Staff(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff"

    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    staff_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    position: Mapped[str] = mapped_column(String(128), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(32), nullable=False)


class Teacher(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "teachers"

    staff_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    academic_title: Mapped[str] = mapped_column(String(64), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)


class AcademicYear(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)


class Semester(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semesters"

    academic_year_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    term_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (UniqueConstraint("academic_year_id", "term_number", name="uq_semester_year_term"),)


class Course(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "courses"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    course_type: Mapped[str] = mapped_column(String(32), nullable=False, default="core")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


def require(db: Session, model, identifier: int, name: str):
    row = db.get(model, identifier)
    if row is None:
        raise NotFoundError(name, identifier)
    return row


def list_rows(db: Session, model, **filters):
    stmt = select(model)
    for key, value in filters.items():
        if value is not None:
            stmt = stmt.where(getattr(model, key) == value)
    return list(db.scalars(stmt))
