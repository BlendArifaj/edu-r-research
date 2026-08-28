from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Exam, ExamRegistration, Grade, GradeHistory


class ExamRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, exam_id: int) -> Exam:
        exam = self.db.get(Exam, exam_id)
        if exam is None:
            raise NotFoundError("Exam", exam_id)
        return exam

    def list(self, course_id: int | None = None) -> list[Exam]:
        stmt = select(Exam)
        if course_id is not None:
            stmt = stmt.where(Exam.course_id == course_id)
        return list(self.db.scalars(stmt.order_by(Exam.id)).all())

    def add(self, exam: Exam) -> Exam:
        self.db.add(exam)
        self.db.flush()
        return exam

    def add_registration(self, registration: ExamRegistration) -> ExamRegistration:
        self.db.add(registration)
        self.db.flush()
        return registration

    def has_registration(self, exam_id: int, student_id: int) -> bool:
        stmt = select(ExamRegistration).where(
            ExamRegistration.exam_id == exam_id,
            ExamRegistration.student_id == student_id,
        )
        return self.db.scalar(stmt) is not None


class GradeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, grade_id: int) -> Grade:
        grade = self.db.get(Grade, grade_id)
        if grade is None:
            raise NotFoundError("Grade", grade_id)
        return grade

    def list_for_student(self, student_id: int) -> list[Grade]:
        stmt = select(Grade).where(Grade.student_id == student_id).order_by(Grade.id)
        return list(self.db.scalars(stmt).all())

    def list_for_course(self, course_id: int) -> list[Grade]:
        stmt = select(Grade).where(Grade.course_id == course_id).order_by(Grade.id)
        return list(self.db.scalars(stmt).all())

    def add(self, grade: Grade) -> Grade:
        self.db.add(grade)
        self.db.flush()
        return grade

    def add_history(self, history: GradeHistory) -> GradeHistory:
        self.db.add(history)
        self.db.flush()
        return history

    def history_for(self, grade_id: int) -> list[GradeHistory]:
        stmt = (
            select(GradeHistory)
            .where(GradeHistory.grade_id == grade_id)
            .order_by(GradeHistory.id)
        )
        return list(self.db.scalars(stmt).all())

    def average_for_course(self, course_id: int) -> Decimal | None:
        grades = self.list_for_course(course_id)
        if not grades:
            return None
        total = sum((g.score for g in grades), Decimal("0"))
        return (total / Decimal(len(grades))).quantize(Decimal("0.01"))
