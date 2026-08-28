from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, DomainError
from app.legacy.academic_utils import score_to_letter, weighted_gpa
from app.models import Exam, ExamRegistration, Grade, GradeHistory
from app.repositories import (
    CourseEnrollmentRepository,
    CourseRepository,
    ExamRepository,
    GradeRepository,
    StudentRepository,
    TeacherRepository,
)
from app.schemas import ExamIn, GpaOut, GradeIn, GradeUpdate
from app.services.finance_service import FinanceService


class GradeService:
    """Grade depends on Student, Teacher, Course, Enrollment, and optionally Finance holds."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.exams = ExamRepository(db)
        self.grades = GradeRepository(db)
        self.students = StudentRepository(db)
        self.courses = CourseRepository(db)
        self.teachers = TeacherRepository(db)
        self.enrollments = CourseEnrollmentRepository(db)
        self.finance = FinanceService(db)

    def create_exam(self, data: ExamIn) -> Exam:
        course = self.courses.get(data.course_id)
        if course.semester_id != data.semester_id:
            raise DomainError("exam semester must match the course semester")
        return self.exams.add(Exam(**data.model_dump()))

    def list_exams(self, course_id: int | None = None) -> list[Exam]:
        return self.exams.list(course_id)

    def get_exam(self, exam_id: int) -> Exam:
        return self.exams.get(exam_id)

    def register_for_exam(self, exam_id: int, student_id: int) -> ExamRegistration:
        exam = self.exams.get(exam_id)
        self.students.get(student_id)
        if not self.enrollments.is_enrolled(student_id, exam.course_id):
            raise DomainError("student is not enrolled in the exam course")
        if self.exams.has_registration(exam_id, student_id):
            raise ConflictError("already registered for this exam")
        return self.exams.add_registration(
            ExamRegistration(
                exam_id=exam_id,
                student_id=student_id,
                registered_at=datetime.now(UTC),
            )
        )

    def record_grade(self, data: GradeIn) -> Grade:
        student = self.students.get(data.student_id)
        course = self.courses.get(data.course_id)
        teacher = self.teachers.get(data.recorded_by_teacher_id)
        if course.teacher_id != teacher.id:
            raise DomainError("only the course teacher may record grades")
        if not self.enrollments.is_enrolled(student.id, course.id):
            raise DomainError("cannot grade a student who is not enrolled")
        if data.exam_id is not None:
            exam = self.exams.get(data.exam_id)
            if exam.course_id != course.id:
                raise DomainError("exam does not belong to the course")
        letter = score_to_letter(data.score)
        grade = Grade(
            student_id=student.id,
            course_id=course.id,
            exam_id=data.exam_id,
            semester_id=data.semester_id,
            score=data.score,
            letter=letter,
            recorded_by_teacher_id=teacher.id,
        )
        return self.grades.add(grade)

    def list_grades(self, student_id: int | None = None, course_id: int | None = None) -> list[Grade]:
        if student_id is not None:
            return self.grades.list_for_student(student_id)
        if course_id is not None:
            return self.grades.list_for_course(course_id)
        return []

    def update_grade(self, grade_id: int, data: GradeUpdate, changed_by_user_id: int) -> Grade:
        grade = self.grades.get(grade_id)
        old_score, old_letter = grade.score, grade.letter
        grade.score = data.score
        grade.letter = score_to_letter(data.score)
        self.grades.add_history(
            GradeHistory(
                grade_id=grade.id,
                old_score=old_score,
                new_score=grade.score,
                old_letter=old_letter,
                new_letter=grade.letter,
                changed_by_user_id=changed_by_user_id,
                reason=data.reason,
                changed_at=datetime.now(UTC),
            )
        )
        self.db.flush()
        return grade

    def history(self, grade_id: int) -> list[GradeHistory]:
        self.grades.get(grade_id)
        return self.grades.history_for(grade_id)

    def calculate_gpa(self, student_id: int) -> GpaOut:
        self.students.get(student_id)
        grades = self.grades.list_for_student(student_id)
        pairs: list[tuple[str, int]] = []
        seen_courses: set[int] = set()
        for grade in grades:
            if grade.course_id in seen_courses:
                continue
            seen_courses.add(grade.course_id)
            course = self.courses.get(grade.course_id)
            pairs.append((grade.letter, course.credits))
        return GpaOut(
            student_id=student_id,
            gpa=weighted_gpa(pairs),
            graded_courses=len(pairs),
        )
