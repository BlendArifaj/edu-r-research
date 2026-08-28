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

__all__ = [
    "AcademicCalendarRepository",
    "AttendanceRepository",
    "CourseEnrollmentRepository",
    "CourseRepository",
    "DepartmentRepository",
    "ExamRepository",
    "FacultyRepository",
    "FinanceRepository",
    "GradeRepository",
    "LibraryRepository",
    "SemesterRegistrationRepository",
    "StaffRepository",
    "StudentRepository",
    "TeacherRepository",
    "UserRepository",
]
