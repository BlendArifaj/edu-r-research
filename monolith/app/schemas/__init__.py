from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class FacultyIn(BaseModel):
    code: str
    name: str
    established_year: int | None = None


class FacultyOut(ORMModel):
    id: int
    code: str
    name: str
    established_year: int | None
    dean_staff_id: int | None


class FacultyUpdate(BaseModel):
    name: str | None = None
    dean_staff_id: int | None = None


class DepartmentIn(BaseModel):
    faculty_id: int
    code: str
    name: str


class DepartmentOut(ORMModel):
    id: int
    faculty_id: int
    code: str
    name: str
    head_staff_id: int | None


class StaffIn(BaseModel):
    email: str
    password: str
    full_name: str
    faculty_id: int
    department_id: int | None = None
    staff_number: str
    position: str
    employment_type: str = "full_time"


class StaffOut(ORMModel):
    id: int
    user_id: int
    faculty_id: int
    department_id: int | None
    staff_number: str
    position: str
    employment_type: str


class TeacherIn(BaseModel):
    staff_id: int
    academic_title: str
    specialization: str


class TeacherOut(ORMModel):
    id: int
    staff_id: int
    academic_title: str
    specialization: str


class AcademicYearIn(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearOut(ORMModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_current: bool


class SemesterIn(BaseModel):
    academic_year_id: int
    name: str
    term_number: int
    start_date: date
    end_date: date


class SemesterOut(ORMModel):
    id: int
    academic_year_id: int
    name: str
    term_number: int
    start_date: date
    end_date: date


class CourseIn(BaseModel):
    code: str
    name: str
    faculty_id: int
    department_id: int
    teacher_id: int
    semester_id: int
    credits: int = 6
    course_type: str = "core"
    description: str | None = None


class CourseOut(ORMModel):
    id: int
    code: str
    name: str
    faculty_id: int
    department_id: int
    teacher_id: int
    semester_id: int
    credits: int
    course_type: str


class FacultyStatisticsOut(BaseModel):
    faculty_id: int
    students: int
    courses: int
    grade_average: Decimal
    collected_fees: Decimal
    ledger_net: Decimal


class StudentIn(BaseModel):
    email: str
    password: str
    full_name: str
    student_number: str
    faculty_id: int
    department_id: int
    enrollment_year: int


class StudentUpdate(BaseModel):
    full_name: str | None = None
    department_id: int | None = None
    status: str | None = None


class StudentOut(ORMModel):
    id: int
    user_id: int
    student_number: str
    faculty_id: int
    department_id: int
    enrollment_year: int
    status: str


class SemesterRegistrationIn(BaseModel):
    semester_id: int


class SemesterRegistrationOut(ORMModel):
    id: int
    student_id: int
    semester_id: int
    status: str
    registered_at: datetime


class EnrollmentIn(BaseModel):
    course_id: int


class EnrollmentOut(ORMModel):
    id: int
    student_id: int
    course_id: int
    semester_id: int
    status: str
    enrolled_at: datetime


class StudentOverviewOut(BaseModel):
    student: StudentOut
    gpa: Decimal
    account_balance: Decimal
    attendance_rate: Decimal
    active_loans: int
    enrolled_courses: int


class ExamIn(BaseModel):
    course_id: int
    semester_id: int
    exam_type: str = "final"
    scheduled_at: datetime
    max_score: Decimal = Decimal("100")


class ExamOut(ORMModel):
    id: int
    course_id: int
    semester_id: int
    exam_type: str
    scheduled_at: datetime
    max_score: Decimal


class ExamRegistrationIn(BaseModel):
    student_id: int


class GradeIn(BaseModel):
    student_id: int
    course_id: int
    exam_id: int | None = None
    semester_id: int
    score: Decimal
    recorded_by_teacher_id: int


class GradeUpdate(BaseModel):
    score: Decimal
    reason: str = "correction"


class GradeOut(ORMModel):
    id: int
    student_id: int
    course_id: int
    exam_id: int | None
    semester_id: int
    score: Decimal
    letter: str
    recorded_by_teacher_id: int


class GradeHistoryOut(ORMModel):
    id: int
    grade_id: int
    old_score: Decimal
    new_score: Decimal
    old_letter: str
    new_letter: str
    reason: str
    changed_at: datetime


class GpaOut(BaseModel):
    student_id: int
    gpa: Decimal
    graded_courses: int


class FeeIn(BaseModel):
    name: str
    amount: Decimal
    fee_type: str
    academic_year_id: int | None = None
    faculty_id: int | None = None


class FeeOut(ORMModel):
    id: int
    name: str
    amount: Decimal
    fee_type: str
    academic_year_id: int | None
    faculty_id: int | None


class InvoiceIn(BaseModel):
    student_id: int
    semester_id: int
    fee_ids: list[int] = Field(min_length=1)


class InvoiceOut(ORMModel):
    id: int
    student_account_id: int
    semester_id: int
    total: Decimal
    status: str
    issued_at: datetime


class PaymentIn(BaseModel):
    invoice_id: int
    amount: Decimal
    method: str = "bank"


class PaymentOut(ORMModel):
    id: int
    invoice_id: int
    student_account_id: int
    amount: Decimal
    method: str
    paid_at: datetime


class AccountOut(ORMModel):
    id: int
    student_id: int
    balance: Decimal


class TransactionOut(ORMModel):
    id: int
    student_account_id: int
    amount: Decimal
    txn_type: str
    reference: str


class FacultyFinanceOut(BaseModel):
    faculty_id: int
    collected_fees: Decimal
    ledger_net: Decimal


class ClassSessionIn(BaseModel):
    course_id: int
    teacher_id: int
    semester_id: int
    scheduled_at: datetime
    topic: str


class ClassSessionOut(ORMModel):
    id: int
    course_id: int
    teacher_id: int
    semester_id: int
    scheduled_at: datetime
    topic: str


class StudentAttendanceIn(BaseModel):
    student_id: int
    status: str = "present"


class StudentAttendanceOut(ORMModel):
    id: int
    class_session_id: int
    student_id: int
    status: str


class StaffAttendanceIn(BaseModel):
    staff_id: int
    work_date: date
    status: str = "present"


class StaffAttendanceOut(ORMModel):
    id: int
    staff_id: int
    work_date: date
    status: str


class MonthlyAttendanceOut(BaseModel):
    year: int
    month: int
    records: int
    present: int
    absent: int


class BookIn(BaseModel):
    isbn: str
    title: str
    author: str
    publisher: str
    year: int


class BookOut(ORMModel):
    id: int
    isbn: str
    title: str
    author: str
    publisher: str
    year: int


class BookCopyIn(BaseModel):
    barcode: str
    location: str = "main"


class BookCopyOut(ORMModel):
    id: int
    book_id: int
    barcode: str
    status: str
    location: str


class LibraryMemberIn(BaseModel):
    user_id: int
    member_type: str
    member_number: str


class LibraryMemberOut(ORMModel):
    id: int
    user_id: int
    member_number: str
    member_type: str


class LoanIn(BaseModel):
    copy_id: int
    member_id: int
    days: int = 14


class LoanOut(ORMModel):
    id: int
    copy_id: int
    member_id: int
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None
    status: str


class ReservationIn(BaseModel):
    book_id: int
    member_id: int


class ReservationOut(ORMModel):
    id: int
    book_id: int
    member_id: int
    reserved_at: datetime
    status: str
