from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, DomainError
from app.legacy.academic_utils import score_to_letter, weighted_gpa
from app.schemas import ExamIn, GpaOut, GradeIn, GradeUpdate
from common.http import Peers
from grade.models import (
    CourseProjection,
    Exam,
    ExamRegistration,
    Grade,
    GradeHistory,
    faculty_average,
    require_exam,
    require_grade,
)


class GradeService:
    def __init__(self, db: Session, peers: Peers) -> None:
        self.db = db
        self.peers = peers

    def create_exam(self, data: ExamIn) -> Exam:
        course = self._course(data.course_id)
        if int(course["semester_id"]) != data.semester_id:
            raise DomainError("exam semester must match the course semester")
        exam = Exam(**data.model_dump())
        self.db.add(exam)
        self.db.flush()
        return exam

    def list_exams(self, course_id: int | None = None) -> list[Exam]:
        stmt = select(Exam)
        if course_id is not None:
            stmt = stmt.where(Exam.course_id == course_id)
        return list(self.db.scalars(stmt))

    def get_exam(self, exam_id: int) -> Exam:
        return require_exam(self.db, exam_id)

    def register_for_exam(self, exam_id: int, student_id: int) -> ExamRegistration:
        exam = self.get_exam(exam_id)
        self.peers.call("student", "GET", f"/internal/students/{student_id}")
        enrolled = self.peers.call(
            "student",
            "GET",
            "/internal/enrollments",
            params={"student_id": student_id, "course_id": exam.course_id},
        )
        if not enrolled.get("enrolled"):
            raise DomainError("student is not enrolled in the exam course")
        exists = self.db.scalar(
            select(ExamRegistration).where(
                ExamRegistration.exam_id == exam_id,
                ExamRegistration.student_id == student_id,
            )
        )
        if exists:
            raise ConflictError("already registered for this exam")
        row = ExamRegistration(exam_id=exam_id, student_id=student_id, registered_at=datetime.now(UTC))
        self.db.add(row)
        self.db.flush()
        return row

    def record_grade(self, data: GradeIn) -> Grade:
        self.peers.call("student", "GET", f"/internal/students/{data.student_id}")
        course = self._course(data.course_id)
        teacher = self.peers.call("faculty", "GET", f"/internal/teachers/{data.recorded_by_teacher_id}")
        if int(course["teacher_id"]) != int(teacher["id"]):
            raise DomainError("only the course teacher may record grades")
        enrolled = self.peers.call(
            "student",
            "GET",
            "/internal/enrollments",
            params={"student_id": data.student_id, "course_id": data.course_id},
        )
        if not enrolled.get("enrolled"):
            raise DomainError("cannot grade a student who is not enrolled")
        if data.exam_id is not None:
            exam = self.get_exam(data.exam_id)
            if exam.course_id != data.course_id:
                raise DomainError("exam does not belong to the course")
        grade = Grade(
            student_id=data.student_id,
            course_id=data.course_id,
            exam_id=data.exam_id,
            semester_id=data.semester_id,
            score=data.score,
            letter=score_to_letter(data.score),
            recorded_by_teacher_id=int(teacher["id"]),
        )
        self.db.add(grade)
        self.db.flush()
        return grade

    def list_grades(self, student_id: int | None = None, course_id: int | None = None) -> list[Grade]:
        stmt = select(Grade)
        if student_id is not None:
            stmt = stmt.where(Grade.student_id == student_id)
        elif course_id is not None:
            stmt = stmt.where(Grade.course_id == course_id)
        else:
            return []
        return list(self.db.scalars(stmt))

    def update_grade(self, grade_id: int, data: GradeUpdate, changed_by_user_id: int) -> Grade:
        grade = require_grade(self.db, grade_id)
        history = GradeHistory(
            grade_id=grade.id,
            old_score=grade.score,
            new_score=data.score,
            old_letter=grade.letter,
            new_letter=score_to_letter(data.score),
            changed_by_user_id=changed_by_user_id,
            reason=data.reason,
            changed_at=datetime.now(UTC),
        )
        grade.score = data.score
        grade.letter = score_to_letter(data.score)
        self.db.add(history)
        self.db.flush()
        return grade

    def history(self, grade_id: int) -> list[GradeHistory]:
        require_grade(self.db, grade_id)
        return list(self.db.scalars(select(GradeHistory).where(GradeHistory.grade_id == grade_id)))

    def calculate_gpa(self, student_id: int) -> GpaOut:
        self.peers.call("student", "GET", f"/internal/students/{student_id}")
        grades = self.list_grades(student_id=student_id)
        pairs: list[tuple[str, int]] = []
        seen: set[int] = set()
        for grade in grades:
            if grade.course_id in seen:
                continue
            seen.add(grade.course_id)
            course = self._course(grade.course_id)
            pairs.append((grade.letter, int(course["credits"])))
        return GpaOut(student_id=student_id, gpa=weighted_gpa(pairs), graded_courses=len(pairs))

    def faculty_grade_average(self, faculty_id: int):
        return {"average": str(faculty_average(self.db, faculty_id))}

    def _course(self, course_id: int) -> dict:
        projection = self.db.get(CourseProjection, course_id)
        if projection is None:
            payload = self.peers.call("faculty", "GET", f"/internal/courses/{course_id}")
            projection = CourseProjection(
                id=int(payload["id"]),
                faculty_id=int(payload["faculty_id"]),
                teacher_id=int(payload["teacher_id"]),
                semester_id=int(payload["semester_id"]),
                credits=int(payload["credits"]),
            )
            self.db.merge(projection)
            self.db.flush()
            return payload
        return {
            "id": projection.id,
            "faculty_id": projection.faculty_id,
            "teacher_id": projection.teacher_id,
            "semester_id": projection.semester_id,
            "credits": projection.credits,
        }
