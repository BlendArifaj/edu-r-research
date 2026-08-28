from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class Faculty(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "faculties"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    established_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dean_staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id", use_alter=True, name="fk_faculties_dean_staff"),
        nullable=True,
    )

    departments: Mapped[list["Department"]] = relationship(
        back_populates="faculty", foreign_keys="Department.faculty_id"
    )
    staff: Mapped[list["Staff"]] = relationship(
        back_populates="faculty", foreign_keys="Staff.faculty_id"
    )
    courses: Mapped[list["Course"]] = relationship(back_populates="faculty")
    students: Mapped[list["Student"]] = relationship(back_populates="faculty")
    dean: Mapped["Staff | None"] = relationship(foreign_keys=[dean_staff_id], post_update=True)


class Department(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    head_staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id", use_alter=True, name="fk_departments_head_staff"),
        nullable=True,
    )

    faculty: Mapped[Faculty] = relationship(
        back_populates="departments", foreign_keys=[faculty_id]
    )
    staff: Mapped[list["Staff"]] = relationship(
        back_populates="department", foreign_keys="Staff.department_id"
    )
    courses: Mapped[list["Course"]] = relationship(back_populates="department")
    students: Mapped[list["Student"]] = relationship(back_populates="department")
    head: Mapped["Staff | None"] = relationship(foreign_keys=[head_staff_id], post_update=True)

    __table_args__ = (UniqueConstraint("faculty_id", "code", name="uq_department_faculty_code"),)


class Staff(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    staff_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    position: Mapped[str] = mapped_column(String(128), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(32), nullable=False)

    user: Mapped["User"] = relationship(back_populates="staff")
    faculty: Mapped[Faculty] = relationship(back_populates="staff", foreign_keys=[faculty_id])
    department: Mapped[Department | None] = relationship(
        back_populates="staff", foreign_keys=[department_id]
    )
    teacher: Mapped["Teacher | None"] = relationship(back_populates="staff", uselist=False)


class Teacher(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "teachers"

    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), unique=True, nullable=False)
    academic_title: Mapped[str] = mapped_column(String(64), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)

    staff: Mapped[Staff] = relationship(back_populates="teacher")
    courses: Mapped[list["Course"]] = relationship(back_populates="teacher")


class AcademicYear(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)

    semesters: Mapped[list["Semester"]] = relationship(back_populates="academic_year")


class Semester(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semesters"

    academic_year_id: Mapped[int] = mapped_column(
        ForeignKey("academic_years.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    term_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    academic_year: Mapped[AcademicYear] = relationship(back_populates="semesters")
    courses: Mapped[list["Course"]] = relationship(back_populates="semester")

    __table_args__ = (
        UniqueConstraint("academic_year_id", "term_number", name="uq_semester_year_term"),
    )


class Course(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "courses"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"), nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False, index=True
    )
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False, index=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    course_type: Mapped[str] = mapped_column(String(32), nullable=False, default="core")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    faculty: Mapped[Faculty] = relationship(back_populates="courses")
    department: Mapped[Department] = relationship(back_populates="courses")
    teacher: Mapped[Teacher] = relationship(back_populates="courses")
    semester: Mapped[Semester] = relationship(back_populates="courses")
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(back_populates="course")
    exams: Mapped[list["Exam"]] = relationship(back_populates="course")
    class_sessions: Mapped[list["ClassSession"]] = relationship(back_populates="course")
