from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
from common.auth import require_user
from common.peers import get_peers
from student.deps import get_db
from student.service import StudentService

router = APIRouter()
internal = APIRouter(prefix="/internal")


def _service(db: Session = Depends(get_db)) -> StudentService:
    return StudentService(db, get_peers())


@router.post("/api/v1/students", response_model=StudentOut, status_code=201)
def create_student(
    payload: StudentIn, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return service.create_student(payload)


@router.get("/api/v1/students", response_model=list[StudentOut])
def list_students(
    faculty_id: int | None = None,
    _: dict = Depends(require_user),
    service: StudentService = Depends(_service),
):
    return service.list_students(faculty_id)


@router.get("/api/v1/students/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return service.get_student(student_id)


@router.patch("/api/v1/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    _: dict = Depends(require_user),
    service: StudentService = Depends(_service),
):
    return service.update_student(student_id, payload)


@router.get("/api/v1/students/{student_id}/overview", response_model=StudentOverviewOut)
def student_overview(
    student_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return service.overview(student_id)


@router.post(
    "/api/v1/students/{student_id}/semester-registrations",
    response_model=SemesterRegistrationOut,
    status_code=201,
)
def register_semester(
    student_id: int,
    payload: SemesterRegistrationIn,
    _: dict = Depends(require_user),
    service: StudentService = Depends(_service),
):
    return service.register_semester(student_id, payload)


@router.get(
    "/api/v1/students/{student_id}/semester-registrations",
    response_model=list[SemesterRegistrationOut],
)
def list_registrations(
    student_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return service.list_registrations(student_id)


@router.post(
    "/api/v1/students/{student_id}/enrollments",
    response_model=EnrollmentOut,
    status_code=201,
)
def enroll(
    student_id: int,
    payload: EnrollmentIn,
    _: dict = Depends(require_user),
    service: StudentService = Depends(_service),
):
    return service.enroll(student_id, payload)


@router.get("/api/v1/students/{student_id}/enrollments", response_model=list[EnrollmentOut])
def list_enrollments(
    student_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return service.list_enrollments(student_id)


@router.get("/api/v1/students/{student_id}/courses", response_model=list[CourseOut])
def list_student_courses(
    student_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return service.list_student_courses(student_id)


@internal.get("/students/by-user/{user_id}")
def internal_by_user(
    user_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    student = service.by_user(user_id)
    if student is None:
        return {"id": None, "status": None}
    return {"id": student.id, "status": student.status, "user_id": student.user_id}


@internal.get("/students/{student_id}")
def internal_student(
    student_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    student = service.get_student(student_id)
    return {
        "id": student.id,
        "user_id": student.user_id,
        "faculty_id": student.faculty_id,
        "status": student.status,
        "student_number": student.student_number,
    }


@internal.get("/enrollments")
def internal_enrolled(
    student_id: int,
    course_id: int,
    _: dict = Depends(require_user),
    service: StudentService = Depends(_service),
):
    return {"enrolled": service.enrolled(student_id, course_id)}


@internal.get("/count")
def internal_count(
    faculty_id: int, _: dict = Depends(require_user), service: StudentService = Depends(_service)
):
    return {"count": service.count_for_faculty(faculty_id)}
