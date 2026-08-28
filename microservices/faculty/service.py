from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.schemas import (
    AcademicYearIn,
    CourseIn,
    DepartmentIn,
    FacultyIn,
    FacultyStatisticsOut,
    FacultyUpdate,
    SemesterIn,
    StaffIn,
    TeacherIn,
)
from common.http import Peers
from faculty.models import (
    AcademicYear,
    Course,
    Department,
    Faculty,
    Semester,
    Staff,
    Teacher,
    list_rows,
    require,
)


class FacultyService:
    def __init__(self, db: Session, peers: Peers) -> None:
        self.db = db
        self.peers = peers

    def create_faculty(self, data: FacultyIn) -> Faculty:
        row = Faculty(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_faculties(self) -> list[Faculty]:
        return list_rows(self.db, Faculty)

    def get_faculty(self, faculty_id: int) -> Faculty:
        return require(self.db, Faculty, faculty_id, "Faculty")

    def update_faculty(self, faculty_id: int, data: FacultyUpdate) -> Faculty:
        faculty = self.get_faculty(faculty_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(faculty, key, value)
        self.db.flush()
        return faculty

    def create_department(self, data: DepartmentIn) -> Department:
        self.get_faculty(data.faculty_id)
        row = Department(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_departments(self, faculty_id: int | None = None) -> list[Department]:
        return list_rows(self.db, Department, faculty_id=faculty_id)

    def create_staff(self, data: StaffIn) -> Staff:
        self.get_faculty(data.faculty_id)
        user = self.peers.call(
            "identity",
            "POST",
            "/internal/users",
            json={
                "email": data.email,
                "password": data.password,
                "full_name": data.full_name,
                "role": "staff",
            },
        )
        row = Staff(
            user_id=int(user["id"]),
            faculty_id=data.faculty_id,
            department_id=data.department_id,
            staff_number=data.staff_number,
            position=data.position,
            employment_type=data.employment_type,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_staff(self, faculty_id: int | None = None) -> list[Staff]:
        return list_rows(self.db, Staff, faculty_id=faculty_id)

    def get_staff(self, staff_id: int) -> Staff:
        return require(self.db, Staff, staff_id, "Staff")

    def create_teacher(self, data: TeacherIn) -> Teacher:
        staff = self.get_staff(data.staff_id)
        existing = list_rows(self.db, Teacher, staff_id=staff.id)
        if existing:
            raise ConflictError("staff already has a teacher profile")
        self.peers.call(
            "identity",
            "PATCH",
            f"/internal/users/{staff.user_id}",
            json={"role": "teacher"},
        )
        row = Teacher(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_teachers(self) -> list[Teacher]:
        return list_rows(self.db, Teacher)

    def get_teacher(self, teacher_id: int) -> Teacher:
        return require(self.db, Teacher, teacher_id, "Teacher")

    def create_course(self, data: CourseIn) -> Course:
        self.get_faculty(data.faculty_id)
        require(self.db, Department, data.department_id, "Department")
        self.get_teacher(data.teacher_id)
        self.get_semester(data.semester_id)
        row = Course(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_courses(self, faculty_id: int | None = None, semester_id: int | None = None):
        return list_rows(self.db, Course, faculty_id=faculty_id, semester_id=semester_id)

    def get_course(self, course_id: int) -> Course:
        return require(self.db, Course, course_id, "Course")

    def create_academic_year(self, data: AcademicYearIn) -> AcademicYear:
        row = AcademicYear(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_academic_years(self) -> list[AcademicYear]:
        return list_rows(self.db, AcademicYear)

    def create_semester(self, data: SemesterIn) -> Semester:
        require(self.db, AcademicYear, data.academic_year_id, "AcademicYear")
        row = Semester(**data.model_dump())
        self.db.add(row)
        self.db.flush()
        return row

    def list_semesters(self) -> list[Semester]:
        return list_rows(self.db, Semester)

    def get_semester(self, semester_id: int) -> Semester:
        return require(self.db, Semester, semester_id, "Semester")

    def get_department(self, department_id: int) -> Department:
        return require(self.db, Department, department_id, "Department")

    def statistics(self, faculty_id: int) -> FacultyStatisticsOut:
        self.get_faculty(faculty_id)
        students = self.peers.call("student", "GET", "/internal/count", params={"faculty_id": faculty_id})
        grades = self.peers.call(
            "grade", "GET", "/internal/faculty-average", params={"faculty_id": faculty_id}
        )
        finance = self.peers.call("finance", "GET", f"/internal/faculty-summary/{faculty_id}")
        courses = list_rows(self.db, Course, faculty_id=faculty_id)
        return FacultyStatisticsOut(
            faculty_id=faculty_id,
            students=int(students["count"]),
            courses=len(courses),
            grade_average=Decimal(str(grades["average"])),
            collected_fees=Decimal(str(finance["collected_fees"])),
            ledger_net=Decimal(str(finance["ledger_net"])),
        )

    def staff_user_ids(self) -> set[int]:
        return {row.user_id for row in self.list_staff()}
