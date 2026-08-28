from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import AcademicYear, Course, Department, Faculty, Semester, Staff, Teacher


class FacultyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, faculty_id: int) -> Faculty:
        faculty = self.db.get(Faculty, faculty_id)
        if faculty is None:
            raise NotFoundError("Faculty", faculty_id)
        return faculty

    def list(self) -> list[Faculty]:
        return list(self.db.scalars(select(Faculty).order_by(Faculty.id)).all())

    def add(self, faculty: Faculty) -> Faculty:
        self.db.add(faculty)
        self.db.flush()
        return faculty


class DepartmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, department_id: int) -> Department:
        department = self.db.get(Department, department_id)
        if department is None:
            raise NotFoundError("Department", department_id)
        return department

    def list_all(self) -> list[Department]:
        return list(self.db.scalars(select(Department).order_by(Department.id)).all())

    def list_for_faculty(self, faculty_id: int) -> list[Department]:
        stmt = select(Department).where(Department.faculty_id == faculty_id).order_by(Department.id)
        return list(self.db.scalars(stmt).all())

    def add(self, department: Department) -> Department:
        self.db.add(department)
        self.db.flush()
        return department


class StaffRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, staff_id: int) -> Staff:
        staff = self.db.get(Staff, staff_id)
        if staff is None:
            raise NotFoundError("Staff", staff_id)
        return staff

    def list(self, faculty_id: int | None = None) -> list[Staff]:
        stmt = select(Staff)
        if faculty_id is not None:
            stmt = stmt.where(Staff.faculty_id == faculty_id)
        return list(self.db.scalars(stmt.order_by(Staff.id)).all())

    def add(self, staff: Staff) -> Staff:
        self.db.add(staff)
        self.db.flush()
        return staff


class TeacherRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, teacher_id: int) -> Teacher:
        teacher = self.db.get(Teacher, teacher_id)
        if teacher is None:
            raise NotFoundError("Teacher", teacher_id)
        return teacher

    def get_by_staff_id(self, staff_id: int) -> Teacher | None:
        return self.db.scalar(select(Teacher).where(Teacher.staff_id == staff_id))

    def list(self) -> list[Teacher]:
        return list(self.db.scalars(select(Teacher).order_by(Teacher.id)).all())

    def add(self, teacher: Teacher) -> Teacher:
        self.db.add(teacher)
        self.db.flush()
        return teacher


class CourseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, course_id: int) -> Course:
        course = self.db.get(Course, course_id)
        if course is None:
            raise NotFoundError("Course", course_id)
        return course

    def list(self, faculty_id: int | None = None, semester_id: int | None = None) -> list[Course]:
        stmt = select(Course)
        if faculty_id is not None:
            stmt = stmt.where(Course.faculty_id == faculty_id)
        if semester_id is not None:
            stmt = stmt.where(Course.semester_id == semester_id)
        return list(self.db.scalars(stmt.order_by(Course.id)).all())

    def add(self, course: Course) -> Course:
        self.db.add(course)
        self.db.flush()
        return course


class AcademicCalendarRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_year(self, academic_year_id: int) -> AcademicYear:
        year = self.db.get(AcademicYear, academic_year_id)
        if year is None:
            raise NotFoundError("AcademicYear", academic_year_id)
        return year

    def list_years(self) -> list[AcademicYear]:
        return list(self.db.scalars(select(AcademicYear).order_by(AcademicYear.id)).all())

    def add_year(self, year: AcademicYear) -> AcademicYear:
        self.db.add(year)
        self.db.flush()
        return year

    def get_semester(self, semester_id: int) -> Semester:
        semester = self.db.get(Semester, semester_id)
        if semester is None:
            raise NotFoundError("Semester", semester_id)
        return semester

    def list_semesters(self) -> list[Semester]:
        return list(self.db.scalars(select(Semester).order_by(Semester.id)).all())

    def add_semester(self, semester: Semester) -> Semester:
        self.db.add(semester)
        self.db.flush()
        return semester
