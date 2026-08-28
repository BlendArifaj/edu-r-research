from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import (
    AcademicYearIn,
    AcademicYearOut,
    CourseIn,
    CourseOut,
    DepartmentIn,
    DepartmentOut,
    FacultyIn,
    FacultyOut,
    FacultyStatisticsOut,
    FacultyUpdate,
    SemesterIn,
    SemesterOut,
    StaffIn,
    StaffOut,
    TeacherIn,
    TeacherOut,
)
from common.auth import require_user
from common.peers import get_peers
from faculty.deps import get_db
from faculty.service import FacultyService

router = APIRouter()
internal = APIRouter(prefix="/internal")


def _service(db: Session = Depends(get_db)) -> FacultyService:
    return FacultyService(db, get_peers())


@router.post("/api/v1/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(
    payload: FacultyIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_faculty(payload)


@router.get("/api/v1/faculties", response_model=list[FacultyOut])
def list_faculties(_: dict = Depends(require_user), service: FacultyService = Depends(_service)):
    return service.list_faculties()


@router.get("/api/v1/faculties/{faculty_id}", response_model=FacultyOut)
def get_faculty(
    faculty_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.get_faculty(faculty_id)


@router.patch("/api/v1/faculties/{faculty_id}", response_model=FacultyOut)
def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    _: dict = Depends(require_user),
    service: FacultyService = Depends(_service),
):
    return service.update_faculty(faculty_id, payload)


@router.get("/api/v1/faculties/{faculty_id}/statistics", response_model=FacultyStatisticsOut)
def faculty_statistics(
    faculty_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.statistics(faculty_id)


@router.post("/api/v1/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_department(payload)


@router.get("/api/v1/departments", response_model=list[DepartmentOut])
def list_departments(
    faculty_id: int | None = None,
    _: dict = Depends(require_user),
    service: FacultyService = Depends(_service),
):
    return service.list_departments(faculty_id)


@router.post("/api/v1/staff", response_model=StaffOut, status_code=201)
def create_staff(
    payload: StaffIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_staff(payload)


@router.get("/api/v1/staff", response_model=list[StaffOut])
def list_staff(
    faculty_id: int | None = None,
    _: dict = Depends(require_user),
    service: FacultyService = Depends(_service),
):
    return service.list_staff(faculty_id)


@router.post("/api/v1/teachers", response_model=TeacherOut, status_code=201)
def create_teacher(
    payload: TeacherIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_teacher(payload)


@router.get("/api/v1/teachers", response_model=list[TeacherOut])
def list_teachers(_: dict = Depends(require_user), service: FacultyService = Depends(_service)):
    return service.list_teachers()


@router.get("/api/v1/teachers/{teacher_id}", response_model=TeacherOut)
def get_teacher(
    teacher_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.get_teacher(teacher_id)


@router.post("/api/v1/courses", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_course(payload)


@router.get("/api/v1/courses", response_model=list[CourseOut])
def list_courses(
    faculty_id: int | None = None,
    semester_id: int | None = None,
    _: dict = Depends(require_user),
    service: FacultyService = Depends(_service),
):
    return service.list_courses(faculty_id, semester_id)


@router.get("/api/v1/courses/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.get_course(course_id)


@router.post("/api/v1/academic-years", response_model=AcademicYearOut, status_code=201)
def create_academic_year(
    payload: AcademicYearIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_academic_year(payload)


@router.get("/api/v1/academic-years", response_model=list[AcademicYearOut])
def list_academic_years(_: dict = Depends(require_user), service: FacultyService = Depends(_service)):
    return service.list_academic_years()


@router.post("/api/v1/semesters", response_model=SemesterOut, status_code=201)
def create_semester(
    payload: SemesterIn, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    return service.create_semester(payload)


@router.get("/api/v1/semesters", response_model=list[SemesterOut])
def list_semesters(_: dict = Depends(require_user), service: FacultyService = Depends(_service)):
    return service.list_semesters()


@internal.get("/courses/{course_id}")
def internal_course(
    course_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    course = service.get_course(course_id)
    return {
        "id": course.id,
        "faculty_id": course.faculty_id,
        "department_id": course.department_id,
        "teacher_id": course.teacher_id,
        "semester_id": course.semester_id,
        "credits": course.credits,
        "code": course.code,
        "name": course.name,
    }


@internal.get("/teachers/{teacher_id}")
def internal_teacher(
    teacher_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    teacher = service.get_teacher(teacher_id)
    return {
        "id": teacher.id,
        "staff_id": teacher.staff_id,
        "academic_title": teacher.academic_title,
        "specialization": teacher.specialization,
    }


@internal.get("/staff/{staff_id}")
def internal_staff(
    staff_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    staff = service.get_staff(staff_id)
    return {"id": staff.id, "user_id": staff.user_id, "faculty_id": staff.faculty_id}


@internal.get("/staff-user-ids")
def internal_staff_user_ids(_: dict = Depends(require_user), service: FacultyService = Depends(_service)):
    return {"user_ids": sorted(service.staff_user_ids())}


@internal.get("/semesters/{semester_id}")
def internal_semester(
    semester_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    semester = service.get_semester(semester_id)
    return {"id": semester.id, "academic_year_id": semester.academic_year_id, "name": semester.name}


@internal.get("/faculties/{faculty_id}")
def internal_faculty(
    faculty_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    faculty = service.get_faculty(faculty_id)
    return {"id": faculty.id, "code": faculty.code, "name": faculty.name}


@internal.get("/departments/{department_id}")
def internal_department(
    department_id: int, _: dict = Depends(require_user), service: FacultyService = Depends(_service)
):
    department = service.get_department(department_id)
    return {
        "id": department.id,
        "faculty_id": department.faculty_id,
        "code": department.code,
        "name": department.name,
    }
