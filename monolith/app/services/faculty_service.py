from sqlalchemy.orm import Session

from app.exceptions import ConflictError
from app.legacy.report_builder import ReportBuilder
from app.models import AcademicYear, Course, Department, Faculty, Semester, Staff, Teacher, User
from app.models.enums import UserRole
from app.repositories import (
    AcademicCalendarRepository,
    CourseRepository,
    DepartmentRepository,
    FacultyRepository,
    FinanceRepository,
    StaffRepository,
    TeacherRepository,
    UserRepository,
)
from app.schemas import (
    AcademicYearIn,
    CourseIn,
    DepartmentIn,
    FacultyFinanceOut,
    FacultyIn,
    FacultyStatisticsOut,
    FacultyUpdate,
    SemesterIn,
    StaffIn,
    TeacherIn,
)
from app.security import hash_password


class FacultyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.faculties = FacultyRepository(db)
        self.departments = DepartmentRepository(db)
        self.staff_repo = StaffRepository(db)
        self.teachers = TeacherRepository(db)
        self.courses = CourseRepository(db)
        self.calendar = AcademicCalendarRepository(db)
        self.users = UserRepository(db)

    def create_faculty(self, data: FacultyIn) -> Faculty:
        return self.faculties.add(Faculty(**data.model_dump()))

    def list_faculties(self) -> list[Faculty]:
        return self.faculties.list()

    def get_faculty(self, faculty_id: int) -> Faculty:
        return self.faculties.get(faculty_id)

    def update_faculty(self, faculty_id: int, data: FacultyUpdate) -> Faculty:
        faculty = self.faculties.get(faculty_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(faculty, key, value)
        self.db.flush()
        return faculty

    def create_department(self, data: DepartmentIn) -> Department:
        self.faculties.get(data.faculty_id)
        return self.departments.add(Department(**data.model_dump()))

    def list_departments(self, faculty_id: int | None = None) -> list[Department]:
        if faculty_id is None:
            return self.departments.list_all()
        return self.departments.list_for_faculty(faculty_id)

    def create_staff(self, data: StaffIn) -> Staff:
        if self.users.get_by_email(data.email):
            raise ConflictError("email already registered")
        self.faculties.get(data.faculty_id)
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.STAFF,
        )
        self.users.add(user)
        staff = Staff(
            user_id=user.id,
            faculty_id=data.faculty_id,
            department_id=data.department_id,
            staff_number=data.staff_number,
            position=data.position,
            employment_type=data.employment_type,
        )
        return self.staff_repo.add(staff)

    def list_staff(self, faculty_id: int | None = None) -> list[Staff]:
        return self.staff_repo.list(faculty_id)

    def create_teacher(self, data: TeacherIn) -> Teacher:
        staff = self.staff_repo.get(data.staff_id)
        if self.teachers.get_by_staff_id(staff.id):
            raise ConflictError("staff already has a teacher profile")
        staff.user.role = UserRole.TEACHER
        return self.teachers.add(Teacher(**data.model_dump()))

    def list_teachers(self) -> list[Teacher]:
        return self.teachers.list()

    def get_teacher(self, teacher_id: int) -> Teacher:
        return self.teachers.get(teacher_id)

    def create_course(self, data: CourseIn) -> Course:
        self.faculties.get(data.faculty_id)
        self.departments.get(data.department_id)
        self.teachers.get(data.teacher_id)
        self.calendar.get_semester(data.semester_id)
        return self.courses.add(Course(**data.model_dump()))

    def list_courses(self, faculty_id: int | None = None, semester_id: int | None = None) -> list[Course]:
        return self.courses.list(faculty_id=faculty_id, semester_id=semester_id)

    def get_course(self, course_id: int) -> Course:
        return self.courses.get(course_id)

    def create_academic_year(self, data: AcademicYearIn) -> AcademicYear:
        return self.calendar.add_year(AcademicYear(**data.model_dump()))

    def list_academic_years(self) -> list[AcademicYear]:
        return self.calendar.list_years()

    def create_semester(self, data: SemesterIn) -> Semester:
        self.calendar.get_year(data.academic_year_id)
        return self.calendar.add_semester(Semester(**data.model_dump()))

    def list_semesters(self) -> list[Semester]:
        return self.calendar.list_semesters()

    def get_semester(self, semester_id: int) -> Semester:
        return self.calendar.get_semester(semester_id)


class FacultyStatisticsService:
    """Reads Student, Grade, Finance, and Faculty tables in one administrative use case."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.faculties = FacultyRepository(db)
        self.finance = FinanceRepository(db)
        self.reports = ReportBuilder(db)

    def statistics(self, faculty_id: int) -> FacultyStatisticsOut:
        self.faculties.get(faculty_id)
        headcount = self.reports.faculty_headcount(faculty_id)
        return FacultyStatisticsOut(
            faculty_id=faculty_id,
            students=headcount["students"],
            courses=headcount["courses"],
            grade_average=self.reports.faculty_grade_average(faculty_id),
            collected_fees=self.reports.faculty_collected_fees(faculty_id),
            ledger_net=self.finance.faculty_net(faculty_id),
        )

    def finance_summary(self, faculty_id: int) -> FacultyFinanceOut:
        self.faculties.get(faculty_id)
        return FacultyFinanceOut(
            faculty_id=faculty_id,
            collected_fees=self.reports.faculty_collected_fees(faculty_id),
            ledger_net=self.finance.faculty_net(faculty_id),
        )
