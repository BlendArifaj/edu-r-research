from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    ClassSessionIn,
    ClassSessionOut,
    MonthlyAttendanceOut,
    StaffAttendanceIn,
    StaffAttendanceOut,
    StudentAttendanceIn,
    StudentAttendanceOut,
)
from app.services import AttendanceService

router = APIRouter(tags=["attendance"])


def _attendance(db: Session = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db)


@router.post("/class-sessions", response_model=ClassSessionOut, status_code=201)
def create_session(
    payload: ClassSessionIn,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.create_session(payload)


@router.get("/class-sessions", response_model=list[ClassSessionOut])
def list_sessions(
    course_id: int | None = None,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.list_sessions(course_id)


@router.get("/class-sessions/{session_id}", response_model=ClassSessionOut)
def get_session(
    session_id: int,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.get_session(session_id)


@router.post(
    "/class-sessions/{session_id}/attendance",
    response_model=StudentAttendanceOut,
    status_code=201,
)
def record_attendance(
    session_id: int,
    payload: StudentAttendanceIn,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.record_student_attendance(session_id, payload)


@router.get("/class-sessions/{session_id}/attendance", response_model=list[StudentAttendanceOut])
def list_session_attendance(
    session_id: int,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.list_session_attendance(session_id)


@router.get("/students/{student_id}/attendance", response_model=list[StudentAttendanceOut])
def student_attendance(
    student_id: int,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.list_student_attendance(student_id)


@router.post("/staff-attendance", response_model=StaffAttendanceOut, status_code=201)
def staff_attendance(
    payload: StaffAttendanceIn,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.record_staff_attendance(payload)


@router.get("/staff/{staff_id}/attendance", response_model=list[StaffAttendanceOut])
def list_staff_attendance(
    staff_id: int,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.list_staff_attendance(staff_id)


@router.get("/attendance/monthly-report", response_model=MonthlyAttendanceOut)
def monthly_report(
    year: int,
    month: int,
    _: User = Depends(get_current_user),
    service: AttendanceService = Depends(_attendance),
):
    return service.monthly_report(year, month)
