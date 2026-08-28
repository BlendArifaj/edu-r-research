from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

from app.instrumentation.context import current_trace

_INSTALLED = False


def _tracked(fn: Callable[..., Any], component_id: str) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        trace = current_trace()
        if trace is not None:
            trace.touch_component(component_id)
        return fn(*args, **kwargs)

    return wrapped


def _wrap_class(cls: type, component_id: str) -> None:
    if getattr(cls, "_sems_r_tracked", False):
        return
    for name, attr in list(vars(cls).items()):
        if name.startswith("_") or not callable(attr):
            continue
        if inspect.isclass(attr):
            continue
        setattr(cls, name, _tracked(attr, component_id))
    cls._sems_r_tracked = True  # type: ignore[attr-defined]


def install_component_tracking() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    from app.legacy.report_builder import ReportBuilder
    from app.repositories.attendance_repository import AttendanceRepository
    from app.repositories.faculty_repository import (
        AcademicCalendarRepository,
        CourseRepository,
        DepartmentRepository,
        FacultyRepository,
        StaffRepository,
        TeacherRepository,
    )
    from app.repositories.finance_repository import FinanceRepository
    from app.repositories.grade_repository import ExamRepository, GradeRepository
    from app.repositories.library_repository import LibraryRepository
    from app.repositories.student_repository import (
        CourseEnrollmentRepository,
        SemesterRegistrationRepository,
        StudentRepository,
    )
    from app.repositories.user_repository import UserRepository
    from app.services.attendance_service import AttendanceService
    from app.services.auth_service import AuthService
    from app.services.faculty_service import FacultyService, FacultyStatisticsService
    from app.services.finance_service import FinanceService
    from app.services.grade_service import GradeService
    from app.services.library_service import LibraryService
    from app.services.overview_service import StudentOverviewService
    from app.services.student_service import EnrollmentGateService, StudentService

    classes = [
        AuthService,
        FacultyService,
        FacultyStatisticsService,
        StudentService,
        EnrollmentGateService,
        StudentOverviewService,
        GradeService,
        FinanceService,
        AttendanceService,
        LibraryService,
        ReportBuilder,
        UserRepository,
        FacultyRepository,
        DepartmentRepository,
        StaffRepository,
        TeacherRepository,
        CourseRepository,
        AcademicCalendarRepository,
        StudentRepository,
        SemesterRegistrationRepository,
        CourseEnrollmentRepository,
        ExamRepository,
        GradeRepository,
        FinanceRepository,
        AttendanceRepository,
        LibraryRepository,
    ]
    for cls in classes:
        _wrap_class(cls, cls.__name__)
    _INSTALLED = True
