"""Cross-domain report helper. Intentionally reads multiple functional areas."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Course, Grade, Payment, Student, StudentAccount, StudentAttendance


class ReportBuilder:
    """High-coupling legacy reporter used by faculty statistics and admin dashboards."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def faculty_headcount(self, faculty_id: int) -> dict[str, int]:
        students = self.db.scalar(
            select(func.count()).select_from(Student).where(Student.faculty_id == faculty_id)
        )
        courses = self.db.scalar(
            select(func.count()).select_from(Course).where(Course.faculty_id == faculty_id)
        )
        return {"students": int(students or 0), "courses": int(courses or 0)}

    def faculty_grade_average(self, faculty_id: int) -> Decimal:
        value = self.db.scalar(
            select(func.avg(Grade.score))
            .join(Course, Course.id == Grade.course_id)
            .where(Course.faculty_id == faculty_id)
        )
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    def faculty_collected_fees(self, faculty_id: int) -> Decimal:
        value = self.db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .join(StudentAccount, StudentAccount.id == Payment.student_account_id)
            .join(Student, Student.id == StudentAccount.student_id)
            .where(Student.faculty_id == faculty_id)
        )
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    def attendance_present_rate(self, student_id: int) -> Decimal:
        total = self.db.scalar(
            select(func.count())
            .select_from(StudentAttendance)
            .where(StudentAttendance.student_id == student_id)
        )
        present = self.db.scalar(
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
