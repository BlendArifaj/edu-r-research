from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import (
    ClassSessionIn,
    ClassSessionOut,
    MonthlyAttendanceOut,
    StaffAttendanceIn,
    StaffAttendanceOut,
    StudentAttendanceIn,
    StudentAttendanceOut,
)
from attendance.deps import get_db
from attendance.service import AttendanceService
from common.auth import require_user
from common.peers import get_peers

router = APIRouter()
internal = APIRouter(prefix="/internal")


def _service(db: Session = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db, get_peers())


@router.post("/api/v1/class-sessions", response_model=ClassSessionOut, status_code=201)
def create_session(
    payload: ClassSessionIn, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.create_session(payload)


@router.get("/api/v1/class-sessions", response_model=list[ClassSessionOut])
def list_sessions(
    course_id: int | None = None,
    _: dict = Depends(require_user),
    service: AttendanceService = Depends(_service),
):
    return service.list_sessions(course_id)


@router.get("/api/v1/class-sessions/{session_id}", response_model=ClassSessionOut)
def get_session(
    session_id: int, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.get_session(session_id)


@router.post(
    "/api/v1/class-sessions/{session_id}/attendance",
    response_model=StudentAttendanceOut,
    status_code=201,
)
def record_attendance(
    session_id: int,
    payload: StudentAttendanceIn,
    _: dict = Depends(require_user),
    service: AttendanceService = Depends(_service),
):
    return service.record_student_attendance(session_id, payload)


@router.get("/api/v1/class-sessions/{session_id}/attendance", response_model=list[StudentAttendanceOut])
def list_session_attendance(
    session_id: int, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.list_session_attendance(session_id)


@router.get("/api/v1/students/{student_id}/attendance", response_model=list[StudentAttendanceOut])
def student_attendance(
    student_id: int, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.list_student_attendance(student_id)


@router.post("/api/v1/staff-attendance", response_model=StaffAttendanceOut, status_code=201)
def staff_attendance(
    payload: StaffAttendanceIn, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.record_staff_attendance(payload)


@router.get("/api/v1/staff/{staff_id}/attendance", response_model=list[StaffAttendanceOut])
def list_staff_attendance(
    staff_id: int, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.list_staff_attendance(staff_id)


@router.get("/api/v1/attendance/monthly-report", response_model=MonthlyAttendanceOut)
def monthly_report(
    year: int,
    month: int,
    _: dict = Depends(require_user),
    service: AttendanceService = Depends(_service),
):
    return service.monthly_report(year, month)


@internal.get("/present-rate/{student_id}")
def internal_present_rate(
    student_id: int, _: dict = Depends(require_user), service: AttendanceService = Depends(_service)
):
    return service.student_present_rate(student_id)
