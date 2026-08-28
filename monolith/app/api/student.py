from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    CourseOut,
    EnrollmentIn,
    EnrollmentOut,
    SemesterRegistrationIn,
    SemesterRegistrationOut,
    StudentIn,
    StudentOut,
    StudentOverviewOut,
    StudentUpdate,
)
from app.services import StudentOverviewService, StudentService

router = APIRouter(tags=["student"])


def _students(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(db)


@router.post("/students", response_model=StudentOut, status_code=201)
def create_student(
    payload: StudentIn, _: User = Depends(get_current_user), service: StudentService = Depends(_students)
):
    return service.create_student(payload)


@router.get("/students", response_model=list[StudentOut])
def list_students(
    faculty_id: int | None = None,
    _: User = Depends(get_current_user),
    service: StudentService = Depends(_students),
):
    return service.list_students(faculty_id)


@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int, _: User = Depends(get_current_user), service: StudentService = Depends(_students)
):
    return service.get_student(student_id)


@router.patch("/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    _: User = Depends(get_current_user),
    service: StudentService = Depends(_students),
):
    return service.update_student(student_id, payload)


@router.get("/students/{student_id}/overview", response_model=StudentOverviewOut)
def student_overview(student_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return StudentOverviewService(db).overview(student_id)


@router.post(
    "/students/{student_id}/semester-registrations",
    response_model=SemesterRegistrationOut,
    status_code=201,
)
def register_semester(
    student_id: int,
    payload: SemesterRegistrationIn,
    _: User = Depends(get_current_user),
    service: StudentService = Depends(_students),
):
    return service.register_semester(student_id, payload)


@router.get("/students/{student_id}/semester-registrations", response_model=list[SemesterRegistrationOut])
def list_registrations(
    student_id: int, _: User = Depends(get_current_user), service: StudentService = Depends(_students)
):
    return service.list_registrations(student_id)


@router.post("/students/{student_id}/enrollments", response_model=EnrollmentOut, status_code=201)
def enroll(
    student_id: int,
    payload: EnrollmentIn,
    _: User = Depends(get_current_user),
    service: StudentService = Depends(_students),
):
    return service.enroll(student_id, payload)


@router.get("/students/{student_id}/enrollments", response_model=list[EnrollmentOut])
def list_enrollments(
    student_id: int, _: User = Depends(get_current_user), service: StudentService = Depends(_students)
):
    return service.list_enrollments(student_id)


@router.get("/students/{student_id}/courses", response_model=list[CourseOut])
def list_student_courses(
    student_id: int, _: User = Depends(get_current_user), service: StudentService = Depends(_students)
):
    return service.list_student_courses(student_id)
