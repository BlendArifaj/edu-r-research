from sqlalchemy.orm import Session

from app.legacy.report_builder import ReportBuilder
from app.schemas import StudentOverviewOut, StudentOut
from app.services.finance_service import FinanceService
from app.services.grade_service import GradeService
from app.services.library_service import LibraryService
from app.services.student_service import StudentService


class StudentOverviewService:
    """God-style academic overview spanning student, grade, finance, attendance, library."""

    def __init__(self, db: Session) -> None:
        self.students = StudentService(db)
        self.grades = GradeService(db)
        self.finance = FinanceService(db)
        self.library = LibraryService(db)
        self.reports = ReportBuilder(db)

    def overview(self, student_id: int) -> StudentOverviewOut:
        student = self.students.get_student(student_id)
        member = self.library.library.get_member_by_user(student.user_id)
        active_loans = len(self.library.active_loans(member.id)) if member else 0
        return StudentOverviewOut(
            student=StudentOut.model_validate(student),
            gpa=self.grades.calculate_gpa(student_id).gpa,
            account_balance=self.finance.get_account(student_id).balance,
            attendance_rate=self.reports.attendance_present_rate(student_id),
            active_loans=active_loans,
            enrolled_courses=len(self.students.list_enrollments(student_id)),
        )
