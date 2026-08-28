from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
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
from app.services import FacultyService, FacultyStatisticsService

router = APIRouter(tags=["faculty"])


def _faculty(db: Session = Depends(get_db)) -> FacultyService:
    return FacultyService(db)


@router.post("/faculties", response_model=FacultyOut, status_code=201)
def create_faculty(
    payload: FacultyIn,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.create_faculty(payload)


@router.get("/faculties", response_model=list[FacultyOut])
def list_faculties(_: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)):
    return service.list_faculties()


@router.get("/faculties/{faculty_id}", response_model=FacultyOut)
def get_faculty(
    faculty_id: int, _: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)
):
    return service.get_faculty(faculty_id)


@router.patch("/faculties/{faculty_id}", response_model=FacultyOut)
def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.update_faculty(faculty_id, payload)


@router.get("/faculties/{faculty_id}/statistics", response_model=FacultyStatisticsOut)
def faculty_statistics(
    faculty_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return FacultyStatisticsService(db).statistics(faculty_id)


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentIn,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.create_department(payload)


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    faculty_id: int | None = None,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.list_departments(faculty_id)


@router.post("/staff", response_model=StaffOut, status_code=201)
def create_staff(
    payload: StaffIn, _: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)
):
    return service.create_staff(payload)


@router.get("/staff", response_model=list[StaffOut])
def list_staff(
    faculty_id: int | None = None,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.list_staff(faculty_id)


@router.post("/teachers", response_model=TeacherOut, status_code=201)
def create_teacher(
    payload: TeacherIn,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.create_teacher(payload)


@router.get("/teachers", response_model=list[TeacherOut])
def list_teachers(_: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)):
    return service.list_teachers()


@router.get("/teachers/{teacher_id}", response_model=TeacherOut)
def get_teacher(
    teacher_id: int, _: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)
):
    return service.get_teacher(teacher_id)


@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseIn, _: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)
):
    return service.create_course(payload)


@router.get("/courses", response_model=list[CourseOut])
def list_courses(
    faculty_id: int | None = None,
    semester_id: int | None = None,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.list_courses(faculty_id, semester_id)


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int, _: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)
):
    return service.get_course(course_id)


@router.post("/academic-years", response_model=AcademicYearOut, status_code=201)
def create_academic_year(
    payload: AcademicYearIn,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.create_academic_year(payload)


@router.get("/academic-years", response_model=list[AcademicYearOut])
def list_academic_years(
    _: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)
):
    return service.list_academic_years()


@router.post("/semesters", response_model=SemesterOut, status_code=201)
def create_semester(
    payload: SemesterIn,
    _: User = Depends(get_current_user),
    service: FacultyService = Depends(_faculty),
):
    return service.create_semester(payload)


@router.get("/semesters", response_model=list[SemesterOut])
def list_semesters(_: User = Depends(get_current_user), service: FacultyService = Depends(_faculty)):
    return service.list_semesters()
