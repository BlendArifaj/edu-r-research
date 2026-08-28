from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.exceptions import DomainError
from app.schemas import ClassSessionIn, MonthlyAttendanceOut, StaffAttendanceIn, StudentAttendanceIn
from attendance.models import (
    ClassSession,
    StaffAttendance,
    StudentAttendance,
    present_rate,
    require_session,
)
from common.http import Peers


class AttendanceService:
    def __init__(self, db: Session, peers: Peers) -> None:
        self.db = db
        self.peers = peers

    def create_session(self, data: ClassSessionIn) -> ClassSession:
        course = self.peers.call("faculty", "GET", f"/internal/courses/{data.course_id}")
        teacher = self.peers.call("faculty", "GET", f"/internal/teachers/{data.teacher_id}")
        if int(course["teacher_id"]) != int(teacher["id"]):
            raise DomainError("session teacher must match the course teacher")
        if int(course["semester_id"]) != data.semester_id:
            raise DomainError("session semester must match the course semester")
        row = ClassSession(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_sessions(self, course_id: int | None = None) -> list[ClassSession]:
        stmt = select(ClassSession)
        if course_id is not None:
            stmt = stmt.where(ClassSession.course_id == course_id)
        return list(self.db.scalars(stmt))

    def get_session(self, session_id: int) -> ClassSession:
        return require_session(self.db, session_id)

    def record_student_attendance(self, session_id: int, data: StudentAttendanceIn) -> StudentAttendance:
        session = self.get_session(session_id)
        self.peers.call("student", "GET", f"/internal/students/{data.student_id}")
        enrolled = self.peers.call(
            "student",
            "GET",
            "/internal/enrollments",
            params={"student_id": data.student_id, "course_id": session.course_id},
        )
        if not enrolled.get("enrolled"):
            raise DomainError("student is not enrolled in this course")
        row = StudentAttendance(
            class_session_id=session.id,
            student_id=data.student_id,
            status=data.status,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_session_attendance(self, session_id: int) -> list[StudentAttendance]:
        self.get_session(session_id)
        return list(
            self.db.scalars(
                select(StudentAttendance).where(StudentAttendance.class_session_id == session_id)
            )
        )

    def list_student_attendance(self, student_id: int) -> list[StudentAttendance]:
        self.peers.call("student", "GET", f"/internal/students/{student_id}")
        return list(
            self.db.scalars(select(StudentAttendance).where(StudentAttendance.student_id == student_id))
        )

    def record_staff_attendance(self, data: StaffAttendanceIn) -> StaffAttendance:
        self.peers.call("faculty", "GET", f"/internal/staff/{data.staff_id}")
        row = StaffAttendance(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_staff_attendance(self, staff_id: int) -> list[StaffAttendance]:
        self.peers.call("faculty", "GET", f"/internal/staff/{staff_id}")
        return list(self.db.scalars(select(StaffAttendance).where(StaffAttendance.staff_id == staff_id)))

    def monthly_report(self, year: int, month: int) -> MonthlyAttendanceOut:
        rows = list(
            self.db.scalars(
                select(StudentAttendance)
                .join(ClassSession, ClassSession.id == StudentAttendance.class_session_id)
                .where(
                    extract("year", ClassSession.scheduled_at) == year,
                    extract("month", ClassSession.scheduled_at) == month,
                )
            )
        )
        present = sum(1 for row in rows if row.status in {"present", "late"})
        absent = sum(1 for row in rows if row.status == "absent")
        return MonthlyAttendanceOut(
            year=year, month=month, records=len(rows), present=present, absent=absent
        )

    def student_present_rate(self, student_id: int) -> dict[str, str]:
        return {"rate": str(present_rate(self.db, student_id))}
