from sqlalchemy.orm import Session

from app.exceptions import DomainError
from app.legacy.report_builder import ReportBuilder
from app.models import ClassSession, StaffAttendance, StudentAttendance
from app.repositories import (
    AttendanceRepository,
    CourseEnrollmentRepository,
    CourseRepository,
    StaffRepository,
    StudentRepository,
    TeacherRepository,
)
from app.schemas import ClassSessionIn, MonthlyAttendanceOut, StaffAttendanceIn, StudentAttendanceIn


class AttendanceService:
    """Attendance depends on Student, Teacher, Course, and Enrollment."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.attendance = AttendanceRepository(db)
        self.courses = CourseRepository(db)
        self.teachers = TeacherRepository(db)
        self.students = StudentRepository(db)
        self.staff_repo = StaffRepository(db)
        self.enrollments = CourseEnrollmentRepository(db)
        self.reports = ReportBuilder(db)

    def create_session(self, data: ClassSessionIn) -> ClassSession:
        course = self.courses.get(data.course_id)
        teacher = self.teachers.get(data.teacher_id)
        if course.teacher_id != teacher.id:
            raise DomainError("session teacher must match the course teacher")
        if course.semester_id != data.semester_id:
            raise DomainError("session semester must match the course semester")
        return self.attendance.add_session(ClassSession(**data.model_dump()))

    def list_sessions(self, course_id: int | None = None) -> list[ClassSession]:
        return self.attendance.list_sessions(course_id)

    def get_session(self, session_id: int) -> ClassSession:
        return self.attendance.get_session(session_id)

    def record_student_attendance(self, session_id: int, data: StudentAttendanceIn) -> StudentAttendance:
        session = self.attendance.get_session(session_id)
        student = self.students.get(data.student_id)
        if not self.enrollments.is_enrolled(student.id, session.course_id):
            raise DomainError("student is not enrolled in this course")
        row = StudentAttendance(
            class_session_id=session.id,
            student_id=student.id,
            status=data.status,
        )
        return self.attendance.add_student_attendance(row)

    def list_session_attendance(self, session_id: int) -> list[StudentAttendance]:
        self.attendance.get_session(session_id)
        return self.attendance.list_session_attendance(session_id)

    def list_student_attendance(self, student_id: int) -> list[StudentAttendance]:
        self.students.get(student_id)
        return self.attendance.list_student_attendance(student_id)

    def record_staff_attendance(self, data: StaffAttendanceIn) -> StaffAttendance:
        self.staff_repo.get(data.staff_id)
        return self.attendance.add_staff_attendance(StaffAttendance(**data.model_dump()))

    def list_staff_attendance(self, staff_id: int) -> list[StaffAttendance]:
        self.staff_repo.get(staff_id)
        return self.attendance.list_staff_attendance(staff_id)

    def monthly_report(self, year: int, month: int) -> MonthlyAttendanceOut:
        rows = self.attendance.monthly_student_rows(year, month)
        present = sum(1 for row in rows if row.status in {"present", "late"})
        absent = sum(1 for row in rows if row.status == "absent")
        return MonthlyAttendanceOut(
            year=year, month=month, records=len(rows), present=present, absent=absent
        )
