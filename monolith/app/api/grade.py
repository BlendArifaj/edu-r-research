from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    ExamIn,
    ExamOut,
    ExamRegistrationIn,
    GpaOut,
    GradeHistoryOut,
    GradeIn,
    GradeOut,
    GradeUpdate,
)
from app.services import GradeService

router = APIRouter(tags=["grade"])


def _grades(db: Session = Depends(get_db)) -> GradeService:
    return GradeService(db)


@router.post("/exams", response_model=ExamOut, status_code=201)
def create_exam(
    payload: ExamIn, _: User = Depends(get_current_user), service: GradeService = Depends(_grades)
):
    return service.create_exam(payload)


@router.get("/exams", response_model=list[ExamOut])
def list_exams(
    course_id: int | None = None,
    _: User = Depends(get_current_user),
    service: GradeService = Depends(_grades),
):
    return service.list_exams(course_id)


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, _: User = Depends(get_current_user), service: GradeService = Depends(_grades)):
    return service.get_exam(exam_id)


@router.post("/exams/{exam_id}/registrations", status_code=201)
def register_exam(
    exam_id: int,
    payload: ExamRegistrationIn,
    _: User = Depends(get_current_user),
    service: GradeService = Depends(_grades),
):
    row = service.register_for_exam(exam_id, payload.student_id)
    return {"id": row.id, "exam_id": row.exam_id, "student_id": row.student_id}


@router.post("/grades", response_model=GradeOut, status_code=201)
def record_grade(
    payload: GradeIn, _: User = Depends(get_current_user), service: GradeService = Depends(_grades)
):
    return service.record_grade(payload)


@router.get("/grades", response_model=list[GradeOut])
def list_grades(
    student_id: int | None = None,
    course_id: int | None = None,
    _: User = Depends(get_current_user),
    service: GradeService = Depends(_grades),
):
    return service.list_grades(student_id=student_id, course_id=course_id)


@router.get("/students/{student_id}/grades", response_model=list[GradeOut])
def student_grades(
    student_id: int, _: User = Depends(get_current_user), service: GradeService = Depends(_grades)
):
    return service.list_grades(student_id=student_id)


@router.patch("/grades/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    user: User = Depends(get_current_user),
    service: GradeService = Depends(_grades),
):
    return service.update_grade(grade_id, payload, changed_by_user_id=user.id)


@router.get("/grades/{grade_id}/history", response_model=list[GradeHistoryOut])
def grade_history(
    grade_id: int, _: User = Depends(get_current_user), service: GradeService = Depends(_grades)
):
    return service.history(grade_id)


@router.get("/students/{student_id}/gpa", response_model=GpaOut)
def student_gpa(
    student_id: int, _: User = Depends(get_current_user), service: GradeService = Depends(_grades)
):
    return service.calculate_gpa(student_id)
