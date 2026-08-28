from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import ClassSession, StaffAttendance, StudentAttendance


class AttendanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session(self, session_id: int) -> ClassSession:
        row = self.db.get(ClassSession, session_id)
        if row is None:
            raise NotFoundError("ClassSession", session_id)
        return row

    def list_sessions(self, course_id: int | None = None) -> list[ClassSession]:
        stmt = select(ClassSession)
        if course_id is not None:
            stmt = stmt.where(ClassSession.course_id == course_id)
        return list(self.db.scalars(stmt.order_by(ClassSession.id)).all())

    def add_session(self, session: ClassSession) -> ClassSession:
        self.db.add(session)
        self.db.flush()
        return session

    def add_student_attendance(self, row: StudentAttendance) -> StudentAttendance:
        self.db.add(row)
        self.db.flush()
        return row

    def list_session_attendance(self, session_id: int) -> list[StudentAttendance]:
        stmt = (
            select(StudentAttendance)
            .where(StudentAttendance.class_session_id == session_id)
            .order_by(StudentAttendance.id)
        )
        return list(self.db.scalars(stmt).all())

    def list_student_attendance(self, student_id: int) -> list[StudentAttendance]:
        stmt = (
            select(StudentAttendance)
            .where(StudentAttendance.student_id == student_id)
            .order_by(StudentAttendance.id)
        )
        return list(self.db.scalars(stmt).all())

    def add_staff_attendance(self, row: StaffAttendance) -> StaffAttendance:
        self.db.add(row)
        self.db.flush()
        return row

    def list_staff_attendance(self, staff_id: int) -> list[StaffAttendance]:
        stmt = (
            select(StaffAttendance)
            .where(StaffAttendance.staff_id == staff_id)
            .order_by(StaffAttendance.work_date)
        )
        return list(self.db.scalars(stmt).all())

    def monthly_student_rows(self, year: int, month: int) -> list[StudentAttendance]:
        stmt = (
            select(StudentAttendance)
            .join(ClassSession, ClassSession.id == StudentAttendance.class_session_id)
            .where(
                extract("year", ClassSession.scheduled_at) == year,
                extract("month", ClassSession.scheduled_at) == month,
            )
        )
        return list(self.db.scalars(stmt).all())
