from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
from common.auth import require_user
from common.peers import get_peers
from grade.deps import get_db
from grade.service import GradeService

router = APIRouter()
internal = APIRouter(prefix="/internal")


def _service(db: Session = Depends(get_db)) -> GradeService:
    return GradeService(db, get_peers())


@router.post("/api/v1/exams", response_model=ExamOut, status_code=201)
def create_exam(payload: ExamIn, _: dict = Depends(require_user), service: GradeService = Depends(_service)):
    return service.create_exam(payload)


@router.get("/api/v1/exams", response_model=list[ExamOut])
def list_exams(
    course_id: int | None = None,
    _: dict = Depends(require_user),
    service: GradeService = Depends(_service),
):
    return service.list_exams(course_id)


@router.get("/api/v1/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, _: dict = Depends(require_user), service: GradeService = Depends(_service)):
    return service.get_exam(exam_id)


@router.post("/api/v1/exams/{exam_id}/registrations", status_code=201)
def register_exam(
    exam_id: int,
    payload: ExamRegistrationIn,
    _: dict = Depends(require_user),
    service: GradeService = Depends(_service),
):
    row = service.register_for_exam(exam_id, payload.student_id)
    return {"id": row.id, "exam_id": row.exam_id, "student_id": row.student_id}


@router.post("/api/v1/grades", response_model=GradeOut, status_code=201)
def record_grade(
    payload: GradeIn, _: dict = Depends(require_user), service: GradeService = Depends(_service)
):
    return service.record_grade(payload)


@router.get("/api/v1/grades", response_model=list[GradeOut])
def list_grades(
    student_id: int | None = None,
    course_id: int | None = None,
    _: dict = Depends(require_user),
    service: GradeService = Depends(_service),
):
    return service.list_grades(student_id=student_id, course_id=course_id)


@router.get("/api/v1/students/{student_id}/grades", response_model=list[GradeOut])
def student_grades(
    student_id: int, _: dict = Depends(require_user), service: GradeService = Depends(_service)
):
    return service.list_grades(student_id=student_id)


@router.patch("/api/v1/grades/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    user: dict = Depends(require_user),
    service: GradeService = Depends(_service),
):
    return service.update_grade(grade_id, payload, changed_by_user_id=int(user["user_id"]))


@router.get("/api/v1/grades/{grade_id}/history", response_model=list[GradeHistoryOut])
def grade_history(
    grade_id: int, _: dict = Depends(require_user), service: GradeService = Depends(_service)
):
    return service.history(grade_id)


@router.get("/api/v1/students/{student_id}/gpa", response_model=GpaOut)
def student_gpa(
    student_id: int, _: dict = Depends(require_user), service: GradeService = Depends(_service)
):
    return service.calculate_gpa(student_id)


@internal.get("/faculty-average")
def internal_faculty_average(
    faculty_id: int, _: dict = Depends(require_user), service: GradeService = Depends(_service)
):
    return service.faculty_grade_average(faculty_id)
